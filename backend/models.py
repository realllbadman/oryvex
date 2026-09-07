"""SQLAlchemy ORM models: Product, Order, Booking."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, Text

from backend.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)              # e.g. "Retatrutide"
    category = Column(Text, nullable=False)
    # categories: "advanced-weight-loss","cosmetic-longevity","glp1-agonists",
    #             "growth-hormone-antiaging","healing-recovery","specialty-nad"

    cas_number = Column(Text, nullable=True)
    molecular_formula = Column(Text, nullable=True)
    purity = Column(Text, nullable=True)             # admin-entered, e.g. "≥99% HPLC"
    form = Column(Text, nullable=True)               # "Lyophilized powder"
    storage = Column(Text, nullable=True)

    price = Column(Float, nullable=False)            # base "from" price
    original_price = Column(Float, nullable=True)
    variants = Column(Text, nullable=True)           # JSON: [{"strength":"5mg","price":49},...]

    description = Column(Text, nullable=True)        # research context ONLY, no human-use claims
    research_notes = Column(Text, nullable=True)     # JSON list of bullet strings

    in_stock = Column(Integer, default=1)
    badge = Column(Text, nullable=True)              # "Best Seller","New","Bulk Save"
    image = Column(Text, nullable=True)

    coa_file = Column(Text, nullable=True)           # /static/coa/<file> or None → "COA pending"
    coa_lab = Column(Text, nullable=True)            # admin-entered testing lab name


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    company = Column(Text, nullable=True)

    address = Column(Text, nullable=True)
    city = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    zip = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    freight_region = Column(Text, nullable=True)

    contact_pref = Column(Text, nullable=True)
    best_time = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    items = Column(Text, nullable=False)             # JSON list of order items
    total = Column(Float, nullable=False)
    status = Column(Text, default="pending")

    coupon_code = Column(Text, nullable=True)        # applied discount code, if any
    discount = Column(Float, default=0.0)            # discount amount applied
    payment_method = Column(Text, nullable=True)     # customer's chosen payment method
    shipping_method = Column(Text, nullable=True)    # chosen shipping method label
    insurance = Column(Float, default=0.0)           # shipping insurance add-on ($)

    age_confirmed = Column(Integer, default=0)       # 1 = confirmed 21+ research use
    created_at = Column(DateTime, default=datetime.utcnow)


class Booking(Base):
    """'Ask a question / COA request / bulk quote' inquiries."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)
    email = Column(Text, nullable=False)

    service = Column(Text, default="General Inquiry")
    product_interest = Column(Text, nullable=True)
    details = Column(Text, nullable=True)

    status = Column(Text, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)


class Coupon(Base):
    """Discount codes (applied via ?coupon=CODE and at checkout)."""

    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)     # stored UPPERCASE
    kind = Column(Text, default="percent")               # "percent" | "fixed"
    value = Column(Float, nullable=False)                 # % (0-100) or $ amount
    active = Column(Integer, default=1)
    min_subtotal = Column(Float, default=0.0)            # minimum order subtotal
    expires_at = Column(DateTime, nullable=True)          # None = never expires
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    """Customer product reviews — admin-moderated before they display."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_slug = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)             # 1-5 stars
    title = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    approved = Column(Integer, default=0)                # 1 = shown publicly
    created_at = Column(DateTime, default=datetime.utcnow)
