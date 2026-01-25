from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum as SAEnum, Text, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import relationship
from datetime import datetime
from .db.base import Base
import enum


class RoleEnum(str, enum.Enum):
    owner = 'owner'
    accountant = 'accountant'
    staff = 'staff'


class MemberRoleEnum(str, enum.Enum):
    accountant = 'accountant'
    staff = 'staff'


class TransactionTypeEnum(str, enum.Enum):
    Income = 'Income'
    Expense = 'Expense'


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(SAEnum(RoleEnum), nullable=False, default=RoleEnum.owner)
    created_at = Column(DateTime, default=datetime.utcnow)

    businesses = relationship('Business', back_populates='owner', cascade='all, delete')
    members = relationship('BusinessMember', back_populates='user', cascade='all, delete')


class Business(Base):
    __tablename__ = 'businesses'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship('User', back_populates='businesses')
    members = relationship('BusinessMember', back_populates='business', cascade='all, delete')
    transactions = relationship('Transaction', back_populates='business', cascade='all, delete')
    inventory = relationship('Inventory', back_populates='business', cascade='all, delete')


class BusinessMember(Base):
    __tablename__ = 'business_members'
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(SAEnum(MemberRoleEnum), nullable=False)

    business = relationship('Business', back_populates='members')
    user = relationship('User', back_populates='members')


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    type = Column(SAEnum(TransactionTypeEnum), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    category = Column(String, nullable=True)
    source = Column(String, nullable=True)
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=True)
    used_quantity = Column(Integer, nullable=True, default=0)
    invoice_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship('Business', back_populates='transactions')
    inventory = relationship('Inventory')


class Inventory(Base):
    __tablename__ = 'inventory'
    __table_args__ = (
        UniqueConstraint('business_id', 'item_name', name='uix_business_itemname'),
        CheckConstraint('quantity >= 0', name='ck_inventory_quantity_nonnegative')
    )
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    item_name = Column(String, nullable=False)
    # Optional category for grouping inventory items (new column)
    category = Column(String, nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    # `cost_price` is the canonical per-unit cost for inventory valuation and
    # transaction amount calculation. Keep this field authoritative and
    # non-negative; do not introduce parallel cost fields.
    cost_price = Column(Numeric(12,2), default=0, nullable=False)
    # Use a timezone-aware server_default so SQLAlchemy INSERTs do not include
    # the column value and PostgreSQL can populate it atomically.
    # This matches other tables which also expose `created_at`.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    business = relationship('Business', back_populates='inventory')
