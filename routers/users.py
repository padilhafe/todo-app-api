from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from models import Todos, Users
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=8)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]
BCryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_user(user: UserDependency,
                   db: DbDependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    return db.query(Users).filter(Users.id == user.get("user_id")).first()

@router.put("/me", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: UserDependency,
                          db: DbDependency,
                          user_verification: UserVerification):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    user_model = db.query(Users).filter(Users.id == user.get("user_id")).first()
    
    if not BCryptContext.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Error on password change")
    
    user_model.hashed_password = BCryptContext.hash(user_verification.new_password)
    
    db.add(user_model)
    db.commit()