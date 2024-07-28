from fastapi import FastAPI, status
from .routers import auth, todos, admin, users
from .database import engine
from .models import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "OK"}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)