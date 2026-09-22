from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

import models
import auth
import transactions

from main import app
from models import Users, Transactions


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

models.Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


def override_current_user():
    return {
        "username": "testuser",
        "id": 1
    }


app.dependency_overrides[auth.get_db] = override_get_db
app.dependency_overrides[transactions.get_db] = override_get_db
app.dependency_overrides[auth.get_current_user] = override_current_user


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():

    db = TestingSessionLocal()

    db.query(Transactions).delete()
    db.query(Users).delete()

    test_user = Users(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password="testpassword"
    )

    db.add(test_user)
    db.commit()
    db.close()


def create_test_transaction():

    response = client.post(
        "/transactions",
        json={
            "title": "Lunch",
            "amount": 250,
            "type": "expense",
            "category": "Food",
            "date": "2026-09-22"
        }
    )

    return response


# 1. Get transaction test
def test_get_transactions():

    create_test_transaction()

    response = client.get("/transactions")

    assert response.status_code == 200
    assert len(response.json()) == 1


# 2. Get specific transaction test
def test_get_specific_transaction():

    create_response = create_test_transaction()

    transaction_id = create_response.json()["id"]

    response = client.get(
        f"/transactions/{transaction_id}"
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Lunch"


# 3. Create transaction test
def test_create_transaction():

    response = create_test_transaction()

    assert response.status_code == 200
    assert response.json()["title"] == "Lunch"
    assert response.json()["amount"] == 250
    assert response.json()["owner_id"] == 1


# 4. Update transaction test
def test_update_transaction():

    create_response = create_test_transaction()

    transaction_id = create_response.json()["id"]

    response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "title": "Dinner",
            "amount": 400,
            "type": "expense",
            "category": "Food",
            "date": "2026-09-22"
        }
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Dinner"
    assert response.json()["amount"] == 400


# 5. Delete transaction test
def test_delete_transaction():

    create_response = create_test_transaction()

    transaction_id = create_response.json()["id"]

    response = client.delete(
        f"/transactions/{transaction_id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Transaction deleted successfully"