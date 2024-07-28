from fastapi import APIRouter, Depends, Path, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated
from .auth import get_current_user
from TodoApp.models import Todos
from TodoApp.database import SessionLocal

router = APIRouter(
    prefix="/todos",
    tags=["Todos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=64)
    description: str = Field(min_length=3, max_length=255)
    priority: int = Field(ge=1, le=5)
    complete: bool = False

@router.get("", status_code=status.HTTP_200_OK)
async def read_all(user: UserDependency,
                   db: DbDependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return db.query(Todos).filter(Todos.owner_id == user.get("user_id")).all()

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def read_todo(user: UserDependency, 
                    id: int, 
                    db: DbDependency):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    todo_model = db.query(Todos)\
            .filter(Todos.id == id)\
            .filter(Todos.owner_id == user.get("user_id"))\
            .first()
            
    if todo_model is not None:
        return todo_model
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_todo(user: UserDependency, 
                      todo_request: TodoRequest, 
                      db: DbDependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("user_id"))

    db.add(todo_model)
    db.commit()
    
@router.put("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: UserDependency,
                      db: DbDependency,
                      todo_request: TodoRequest,
                      id: int = Path(gt=0)):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    
    todo_model = db.query(Todos)\
        .filter(Todos.id == id)\
            .filter(Todos.owner_id == user.get("user_id"))\
            .first()
            
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete
    
    db.add(todo_model)
    db.commit()
    
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: UserDependency, 
                      db: DbDependency, 
                      id: int = Path(gt=0)):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    
    todo_model = db.query(Todos)\
        .filter(Todos.id == id)\
            .filter(Todos.owner_id == user.get("user_id"))\
            .first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    
    db.delete(todo_model)
    db.commit()
