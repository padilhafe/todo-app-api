from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError

from models import Users
from database import SessionLocal

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

SECRET_KEY = "gBqnWHO2oKqTsqCngbsQKxgrSKMKY9ru"
ALGORITHM = "HS256"

BCryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2Bearer = OAuth2PasswordBearer(tokenUrl='auth/token') 

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str = Field(min_length=8)
    role: str
    phone_number: str = Field(min_length=11, nullable=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not BCryptContext.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {"sub": username, "user_id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(OAuth2Bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Could not validate credentials.")
        return {
            "username": username,
            "user_id": user_id,
            "user_role": user_role,
        }
        
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials.") from exc
        

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(db: DbDependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=BCryptContext.hash(create_user_request.password),
        role=create_user_request.role,
        is_active=True,
        phone_number = create_user_request.phone_number,
    )

    db.add(create_user_model)
    db.commit()

@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_for_access_token(
                                form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                db: DbDependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Failed authentication.")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}
