import requests
import time

class APIException(Exception):
    pass

class QuizLoader:
    def __init__(self, server_token: str, category: str, size: int = 50, difficulty: str = 'easy'):
        self.category = category
        self.size = size
        self.difficulty = difficulty
        self.token = None
        self.server_token = server_token
    
    def load_quizzes(self):
        pass
# Get 
class OTDBQuizLoader(QuizLoader):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = self.size or 50
        self.BASE_URL = 'https://opentdb.com'
        self.token = self.fetch_token()
        self.fetch_categories()

    def retry_after_delay(self, func):
        time.sleep(5)
        return func()
    
    def fetch_categories(self):
        response = requests.get(url=f'{self.BASE_URL}/api_category.php')
        response_json = response.json()
        self.category_map = {category["name"]: category["id"] for category in response_json['trivia_categories']}
    
    def fetch_token(self):
        response = requests.get(url=f'{self.BASE_URL}/api_token.php?command=request')
        response_json = response.json()
        code = response_json['response_code']
        if code == 5:
            return self.retry_after_delay(self.fetch_token)
        if code == 4:
            return ''
        return response_json['token']
    
    def convert_to_mongoose_schema(self, questions, quiz_number):
        category = self.category or "mix"
        title = f"{category.capitalize()}-questions-{quiz_number}"
        mongoose_quiz = {
            "title": title,
            "time": "30m",  # Set default time to 30 minutes
            "difficulty": questions[0]["difficulty"],
            "category": [category.capitalize()],
            "questions": []
        }

        for question in questions:
            mongoose_quiz["questions"].append({
                "title": question["question"],
                "description": "Replace with appropriate description if available",
                "options": [
                    {"description": question["correct_answer"], "isAnswer": "true"}
                ] + [{"description": option, "isAnswer": "false"} for option in question["incorrect_answers"]]
            })

        return mongoose_quiz
    
    def send_to_server(self, data):
        headers = {'Authorization': f'Bearer {self.server_token}'}        
        response = requests.post(url='http://localhost:4564/quiz/', headers=headers, json=data)
        print(response)
    
    def load_quizzes(self):
        """
        ## This function does the following:
        1. Get token for OTDB
        2. Call the OTDB api
        3. Update the data as per the schema
        4. Send to node server
        """
        self.token = self.fetch_token()
        total_count = 0
        code = 0
        while code != 4:
            response = requests.get(f'{self.BASE_URL}/api.php?token={self.token}{f'&amount={self.size}' if self.size else ''}{f'?category={self.category_map[self.category]}' if self.category else ''}{f'?difficulty={self.difficulty}' if self.difficulty else ''}')
            reponse_json = response.json()
            code = reponse_json['response_code']
            print(code)
            if code == 3:
                self.token = self.fetch_token()
            elif code == 4:
                return dict(total_count=total_count)
            elif code == 5:
                time.sleep(5)
            elif code == 1:
                return dict(total_count=total_count)
            else:
                questions = reponse_json['results']
                quiz_input = self.convert_to_mongoose_schema(questions=questions, quiz_number=total_count+1)
                self.send_to_server(quiz_input)
                total_count+=1

        return dict(total_count=total_count)

        