import re
from typing import Optional


def parse_order_email(subject: str, body: str, email_id: str) -> dict:
    """
    Parse a House of Worktops order confirmation email into structured data.
    Returns dict with keys: order, customer, items.
    All fields default to None on parse failure — never raises.
    """
    return {
        "order": _parse_order(subject, body, email_id),
        "customer": _parse_customer(body),
        "items": _parse_items(body),
    }


def _parse_order(subject: str, body: str, email_id: str) -> dict:
    order_id = _extract_order_id(subject, body)
    date_added = _find(r"Date Added:[ \t]*(\d{2}/\d{2}/\d{4})", body)
    status = _find(r"Order Status:[ \t]*([^\n]+)", body)
    subtotal, vat, grand_total = _parse_totals(body)
    comments = _find(r"The comments for your order are:\n([^\n]+)", body)
    deliver_by = _find(r"Deliver By:[ \t]*([^\n]+)", body) or None
    is_business = _parse_business_flag(body)

    return {
        "order_id": order_id,
        "date_added": date_added,
        "status": status,
        "subtotal": subtotal,
        "vat": vat,
        "grand_total": grand_total,
        "comments": comments,
        "deliver_by": deliver_by,
        "is_business_customer": is_business,
        "raw_email_id": email_id,
    }


def _parse_customer(body: str) -> dict:
    return {
        "name": _find(r"Customer Name:[ \t]*([^\n]+)", body),
        "email": _find(r"Customer Email:[ \t]*([^\n]+)", body),
        "postcode": _find(r"Customer Postcode:[ \t]*([^\n]+)", body),
        "phone": _find(r"Customer Phone:[ \t]*([^\n]+)", body),
    }


def _parse_items(body: str) -> list[dict]:
    """
    Match lines like: 1x Product Name (sku) £9.99
    Handles multiple products per order.
    """
    pattern = r"(\d+)x\s+(.+?)\s+\(([^)]+)\)\s+£([\d.]+)"
    items = []
    for m in re.finditer(pattern, body):
        qty = int(m.group(1))
        name = m.group(2).strip()
        sku = m.group(3).strip()
        price = _to_decimal(m.group(4))
        items.append({
            "product_name": name,
            "product_sku": sku,
            "quantity": qty,
            "unit_price": price,
            "line_total": round(qty * price, 2) if price is not None else None,
        })
    return items


def _parse_totals(body: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Extract subtotal, VAT, and grand total from the Totals section.
    The subtotal label varies (e.g. "Sample Bundle:", "Subtotal:") so we
    capture the first £ amount in the Totals block, then VAT, then Order Total.
    """
    totals_block = re.search(r"Totals\n(.*?)(?:\n\n|\Z)", body, re.DOTALL)
    if not totals_block:
        return None, None, None

    block = totals_block.group(1)
    amounts = re.findall(r"£([\d.]+)", block)
    subtotal = _to_decimal(amounts[0]) if len(amounts) > 0 else None
    vat = _to_decimal(amounts[1]) if len(amounts) > 1 else None
    grand_total = _to_decimal(amounts[2]) if len(amounts) > 2 else None
    return subtotal, vat, grand_total


def _extract_order_id(subject: str, body: str) -> Optional[str]:
    # Try subject first: "House of Worktops - Order 162972" or "...Sample Order 162972"
    m = re.search(r"(?:Sample )?Order\s+(\d+)", subject, re.IGNORECASE)
    if m:
        return m.group(1)
    # Fallback to body
    m = re.search(r"Order ID:\s*(\d+)", body)
    return m.group(1) if m else None


def _parse_business_flag(body: str) -> bool:
    m = re.search(r"Business Customer:[ \t]*([^\n]*)", body)
    if not m:
        return False
    val = m.group(1).strip().lower()
    return val in ("yes", "true", "1")


def _find(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _to_decimal(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None
