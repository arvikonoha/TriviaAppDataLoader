from fastapi import APIRouter, Header
from ..services.quiz import OTDBQuizLoader

quizrouter = APIRouter(prefix="/v1/load")

@quizrouter.post('/')
def load_quiz(token: str=Header(...)):
    loader = OTDBQuizLoader(category='General Knowledge', server_token=token)
    loader.load_quizzes()
    return {'message': 'Successfully loaded the quiz to the server'}