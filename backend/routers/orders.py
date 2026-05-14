import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.memory.db import get_db
from backend.memory.schema import Order, OrderCustomer, OrderItem

logger = logging.getLogger(__name__)

router = APIRouter()


def _serialize_order(o: Order, customer: OrderCustomer | None, items: list[OrderItem]) -> dict:
    return {
        "id": o.id,
        "order_id": o.order_id,
        "date_added": o.date_added,
        "status": o.status,
        "subtotal": float(o.subtotal) if o.subtotal is not None else None,
        "vat": float(o.vat) if o.vat is not None else None,
        "grand_total": float(o.grand_total) if o.grand_total is not None else None,
        "comments": o.comments,
        "deliver_by": o.deliver_by,
        "is_business_customer": o.is_business_customer,
        "raw_email_id": o.raw_email_id,
        "source_email": o.source_email,
        "created_at": o.created_at,
        "customer": {
            "name": customer.name if customer else None,
            "email": customer.email if customer else None,
            "postcode": customer.postcode if customer else None,
            "phone": customer.phone if customer else None,
        } if customer else None,
        "items": [
            {
                "product_name": i.product_name,
                "product_sku": i.product_sku,
                "quantity": i.quantity,
                "unit_price": float(i.unit_price) if i.unit_price is not None else None,
                "line_total": float(i.line_total) if i.line_total is not None else None,
            }
            for i in items
        ],
    }


@router.get("/today")
def orders_today(db: Session = Depends(get_db)):
    from datetime import date, datetime
    today = date.today().strftime("%d/%m/%Y")
    orders = db.query(Order).filter(Order.date_added == today).all()
    total_revenue = sum(float(o.grand_total or 0) for o in orders)
    return {
        "count": len(orders),
        "total_revenue": round(total_revenue, 2),
        "orders": [_slim(o) for o in orders],
    }


@router.get("/summary")
def orders_summary(db: Session = Depends(get_db)):
    all_orders = db.query(Order).all()
    total_orders = len(all_orders)
    total_revenue = sum(float(o.grand_total or 0) for o in all_orders)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0

    # Group by date_added to find highest-volume and highest-revenue days
    from collections import defaultdict
    by_date: dict[str, list] = defaultdict(list)
    for o in all_orders:
        if o.date_added:
            by_date[o.date_added].append(float(o.grand_total or 0))

    highest_orders_date, highest_orders_count = None, 0
    highest_revenue_date, highest_revenue_amount = None, 0.0
    for d, totals in by_date.items():
        if len(totals) > highest_orders_count:
            highest_orders_count = len(totals)
            highest_orders_date = d
        day_rev = sum(totals)
        if day_rev > highest_revenue_amount:
            highest_revenue_amount = day_rev
            highest_revenue_date = d

    # Status breakdown
    status_counts: dict[str, int] = defaultdict(int)
    for o in all_orders:
        status_counts[o.status or "unknown"] += 1

    # Top products by quantity
    items = db.query(OrderItem).all()
    product_qty: dict[str, int] = defaultdict(int)
    for i in items:
        if i.product_name:
            product_qty[i.product_name] += (i.quantity or 0)
    top_products = sorted(product_qty.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": avg_order_value,
        "highest_orders_in_a_day": {"date": highest_orders_date, "count": highest_orders_count},
        "highest_revenue_in_a_day": {"date": highest_revenue_date, "amount": round(highest_revenue_amount, 2)},
        "orders_by_status": dict(status_counts),
        "top_products": [{"product": p, "total_quantity": q} for p, q in top_products],
    }


@router.get("/all")
def orders_all(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    date_from: str | None = None,  # DD/MM/YYYY
    date_to: str | None = None,    # DD/MM/YYYY
    db: Session = Depends(get_db),
):
    query = db.query(Order).order_by(desc(Order.created_at))
    if status:
        query = query.filter(Order.status == status)
    # date_added is stored as DD/MM/YYYY string; filter with string comparison
    if date_from:
        orders = [o for o in query.all() if _date_gte(o.date_added, date_from)]
    else:
        orders = query.all()
    if date_to:
        orders = [o for o in orders if _date_lte(o.date_added, date_to)]

    total = len(orders)
    start = (page - 1) * limit
    page_orders = orders[start: start + limit]

    customers = {
        c.order_id: c
        for c in db.query(OrderCustomer).filter(
            OrderCustomer.order_id.in_([o.order_id for o in page_orders])
        ).all()
    }
    items_map: dict[str, list] = {}
    for i in db.query(OrderItem).filter(
        OrderItem.order_id.in_([o.order_id for o in page_orders])
    ).all():
        items_map.setdefault(i.order_id, []).append(i)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "orders": [
            _serialize_order(o, customers.get(o.order_id), items_map.get(o.order_id, []))
            for o in page_orders
        ],
    }


@router.post("/backfill")
def orders_backfill(db: Session = Depends(get_db)):
    """Fetch all historical HoW order emails and insert any not already in DB.

    Safe to call repeatedly — _save_order_atomic is idempotent on order_id.
    Returns counts: found (order emails), new (inserted), skipped (already in DB).
    """
    from backend.tools.gmail import get_all_emails_by_subject_pattern, is_authenticated
    from backend.tools.order_parser import parse_order_email
    from backend.agents.hedwig import is_order_email, _save_order_atomic

    if not is_authenticated("houseofworktops"):
        return {"error": "houseofworktops account not authenticated — run gmail_auth.py first"}

    emails = get_all_emails_by_subject_pattern("houseofworktops", "House of Worktops")
    order_emails = [e for e in emails if is_order_email(e["subject"], e["sender"])]

    found = len(order_emails)
    new_count = 0
    skipped = 0

    for email in order_emails:
        parsed = parse_order_email(
            email["subject"],
            email.get("full_body", email.get("body_preview", "")),
            email["gmail_id"],
        )
        order_id = (parsed.get("order") or {}).get("order_id")
        if not order_id:
            skipped += 1
            continue
        if db.query(Order).filter(Order.order_id == order_id).first():
            skipped += 1
        else:
            _save_order_atomic(db, parsed, "houseofworktops")
            new_count += 1

    logger.info(f"Backfill complete: found={found} new={new_count} skipped={skipped}")
    return {"found": found, "new": new_count, "skipped": skipped}


@router.get("/{order_id}")
def order_detail(order_id: str, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.order_id == order_id).first()
    if not o:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    customer = db.query(OrderCustomer).filter(OrderCustomer.order_id == order_id).first()
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return _serialize_order(o, customer, items)


def _slim(o: Order) -> dict:
    return {
        "order_id": o.order_id,
        "date_added": o.date_added,
        "status": o.status,
        "grand_total": float(o.grand_total) if o.grand_total is not None else None,
    }


def _date_gte(date_str: str | None, threshold: str) -> bool:
    if not date_str:
        return False
    return _parse_ddmmyyyy(date_str) >= _parse_ddmmyyyy(threshold)


def _date_lte(date_str: str | None, threshold: str) -> bool:
    if not date_str:
        return False
    return _parse_ddmmyyyy(date_str) <= _parse_ddmmyyyy(threshold)


def _parse_ddmmyyyy(s: str):
    from datetime import date
    parts = s.split("/")
    if len(parts) != 3:
        return date.min
    try:
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except ValueError:
        return date.min
