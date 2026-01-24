from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = 'owner'


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class BusinessCreate(BaseModel):
    name: str
    industry: Optional[str]


class BusinessOut(BaseModel):
    id: int
    owner_id: int
    name: str
    industry: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class BusinessWithRole(BusinessOut):
    role: Optional[str]

    class Config:
        orm_mode = True


class TransactionCreate(BaseModel):
    business_id: int
    type: str
    amount: float
    category: Optional[str]


class TransactionUpdate(BaseModel):
    type: Optional[str]
    amount: Optional[float]
    category: Optional[str]
    invoice_url: Optional[str]


class TransactionOut(BaseModel):
    id: int
    business_id: int
    type: str
    amount: float
    category: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class InventoryCreate(BaseModel):
    business_id: int
    item_name: str
    quantity: int
    cost_price: float


class MemberCreate(BaseModel):
    business_id: int
    user_id: int
    role: str


class MemberOut(BaseModel):
    id: int
    business_id: int
    user_id: int
    role: str
    username: Optional[str] = None

    class Config:
        orm_mode = True


class MemberAdd(BaseModel):
    username: str
    role: str


class DashboardOut(BaseModel):
    total_income: Optional[float] = None
    total_expense: Optional[float] = None
    net_profit: Optional[float] = None
    transactions_count: Optional[int] = None
    business_name: str
    role: str

    class Config:
        orm_mode = True


class InventoryOut(BaseModel):
    id: int
    business_id: int
    item_name: str
    quantity: int
    cost_price: float

    class Config:
        orm_mode = True


class SummaryOut(BaseModel):
    income: float = 0.0
    expense: float = 0.0


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
