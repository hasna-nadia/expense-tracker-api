from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from database import SessionLocal
from models import Users


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


bcrypt_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


SECRET_KEY = "expense_tracker_secret_key"
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(
    username: str,
    password: str,
    db: Session
):

    user = db.query(Users).filter(
        Users.username == username
    ).first()

    if not user:
        return False

    if not bcrypt_context.verify(
        password,
        user.hashed_password
    ):
        return False

    return user


def create_access_token(
    username: str,
    user_id: int,
    expires_delta: timedelta
):

    encode = {
        "sub": username,
        "id": user_id
    }

    expires = (
        datetime.now(timezone.utc)
        + expires_delta
    )

    encode.update({
        "exp": expires
    })

    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_bearer)
):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        user_id = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate user"
            )

        return {
            "username": username,
            "id": user_id
        }

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate user"
        )


@router.post("/register")
def register_user(
    user_request: CreateUserRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(Users).filter(
        Users.username == user_request.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    user_model = Users(
        username=user_request.username,
        email=user_request.email,
        hashed_password=bcrypt_context.hash(
            user_request.password
        )
    )

    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return {
        "id": user_model.id,
        "username": user_model.username,
        "email": user_model.email
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        form_data.username,
        form_data.password,
        db
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = create_access_token(
        user.username,
        user.id,
        timedelta(minutes=30)
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }