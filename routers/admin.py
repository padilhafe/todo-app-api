from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from models import Todos
from .auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]

@router.get("/todos", status_code=status.HTTP_200_OK)
async def read_all(user: UserDependency,
                   db: DbDependency):
    
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated or not admin")
    
    return db.query(Todos).all()

@router.delete("/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: UserDependency, 
                      db: DbDependency, 
                      id: int = Path(gt=0)):
    
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated or not admin")
    
    todo_model = db.query(Todos).filter(Todos.id == id).first()
    
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    db.delete(todo_model)
    db.commit()