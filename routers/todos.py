from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import SessionLocal
from typing import Annotated
from models import Todos

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=64)
    description: str = Field(min_length=3, max_length=255)
    priority: int = Field(ge=1, le=5)
    complete: bool = False

@router.get("/todos", status_code=status.HTTP_200_OK)
async def read_all(db: DbDependency):
    return db.query(Todos).all()

@router.get("/todos/{id}", status_code=status.HTTP_200_OK)
async def read_todo(id: int, db: DbDependency):
    todo_model = db.query(Todos).filter(Todos.id == id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

@router.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_todo(todo_request: TodoRequest, db: DbDependency):
    todo_model = Todos(**todo_request.model_dump())

    db.add(todo_model)
    db.commit()
    
@router.put("/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(db: DbDependency,
                      todo_request: TodoRequest,
                      id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == id).first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    
    db.add(todo_model)
    db.commit()
    
@router.delete("/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: DbDependency, id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == id).first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    db.delete(todo_model)
    db.commit()
