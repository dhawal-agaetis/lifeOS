from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric
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
    order_id = Column(String(100))
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    product = Column(Text)
    amount = Column(String(50))
    currency = Column(String(10), default="GBP")
    order_date = Column(DateTime)
    raw_email_id = Column(String(100))  # references emails.gmail_id
    created_at = Column(DateTime, default=datetime.utcnow)
