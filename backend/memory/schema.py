from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey
from backend.memory.db import Base


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(50), nullable=False)
    task = Column(Text, nullable=False)
    result = Column(Text)
    status = Column(String(20), default="success")  # success | error
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # whatsapp | dashboard
    content = Column(Text, nullable=False)
    agent_routed_to = Column(String(50))
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")  # pending | done | failed
    agent = Column(String(50))
    due_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String(100), unique=True, nullable=False)
    account = Column(String(50), nullable=False, default="unknown")  # personal | agaetis | houseofworktops
    subject = Column(Text)
    sender = Column(String(255))
    body_preview = Column(Text)
    parsed_data = Column(Text)  # JSON string
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    date_added = Column(String(20))          # stored as DD/MM/YYYY string from email
    status = Column(String(100))
    subtotal = Column(Numeric(10, 2))
    vat = Column(Numeric(10, 2))
    grand_total = Column(Numeric(10, 2))
    comments = Column(Text)
    deliver_by = Column(String(255))
    is_business_customer = Column(Boolean, default=False)
    raw_email_id = Column(String(100))       # references emails.gmail_id
    source_email = Column(String(50))        # which gmail account
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderCustomer(Base):
    __tablename__ = "order_customers"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), ForeignKey("orders.order_id"), nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(255))
    postcode = Column(String(20))
    phone = Column(String(50))


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(100), ForeignKey("orders.order_id"), nullable=False, index=True)
    product_name = Column(Text)
    product_sku = Column(String(100))
    quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))
    line_total = Column(Numeric(10, 2))
