from fastapi import FastAPI
from .routers.quiz import quizrouter

app = FastAPI()

app.include_router(quizrouter)