from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Transactions
from auth import get_current_user


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


class TransactionRequest(BaseModel):
    title: str
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: str
    date: date


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
def create_transaction(
    transaction_request: TransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    transaction_model = Transactions(
        title=transaction_request.title,
        amount=transaction_request.amount,
        type=transaction_request.type,
        category=transaction_request.category,
        date=transaction_request.date,
        owner_id=current_user["id"]
    )

    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return transaction_model


@router.get("")
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    transactions = db.query(Transactions).filter(
        Transactions.owner_id == current_user["id"]
    ).all()

    return transactions


@router.get("/filter")
def filter_transactions(
    type: str = None,
    category: str = None,
    minimum_amount: float = None,
    maximum_amount: float = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    query = db.query(Transactions).filter(
        Transactions.owner_id == current_user["id"]
    )

    if type:
        query = query.filter(
            Transactions.type == type
        )

    if category:
        query = query.filter(
            Transactions.category == category
        )

    if minimum_amount is not None:
        query = query.filter(
            Transactions.amount >= minimum_amount
        )

    if maximum_amount is not None:
        query = query.filter(
            Transactions.amount <= maximum_amount
        )

    return query.all()

@router.get("/{transaction_id}")
def get_transaction_by_id(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    transaction = db.query(Transactions).filter(
        Transactions.id == transaction_id,
        Transactions.owner_id == current_user["id"]
    ).first()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction_request: TransactionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    transaction = db.query(Transactions).filter(
        Transactions.id == transaction_id,
        Transactions.owner_id == current_user["id"]
    ).first()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction.title = transaction_request.title
    transaction.amount = transaction_request.amount
    transaction.type = transaction_request.type
    transaction.category = transaction_request.category
    transaction.date = transaction_request.date

    db.commit()
    db.refresh(transaction)

    return transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    transaction = db.query(Transactions).filter(
        Transactions.id == transaction_id,
        Transactions.owner_id == current_user["id"]
    ).first()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }