import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from TodoApp.main import app
from TodoApp.database import Base
from TodoApp.routers.todos import get_db, get_current_user
from TodoApp.models import Todos

SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass = StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def overrride_get_current_user():
    return {
        "username": "testuser",
        "user_id": 1,
        "user_role": "admin",
    }
    
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = overrride_get_current_user

client = TestClient(app)

@pytest.fixture(autouse=True)
def test_todo():
    todo = Todos(
        title="Test Todo",
        description="Test todo description",
        priority=5,
        complete=False,
        owner_id=1,
    )

    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    
    yield todo
    
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()

def test_read_all_authenticated():
    response = client.get("/todos")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
                                'title': 'Test Todo', 
                                'description': 'Test todo description', 
                                'complete': False, 
                                'priority': 5, 
                                'id': 1, 
                                'owner_id': 1
                            }]