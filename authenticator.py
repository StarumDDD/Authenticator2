from flask import Flask, redirect, request, session
import requests
from dotenv import load_dotenv
import os
import secrets


load_dotenv()

# Параметры приложения GitLab
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SECRET_KEY = os.getenv('SECRET_KEY')

# Генерация секретного ключа, если он отсутствует
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print(f"New generated SECRET_KEY: {SECRET_KEY}")

app = Flask(__name__)
app.secret_key = SECRET_KEY

GITLAB_BASE_URL = 'https://gitlab.com'


@app.route('/')
def home():
    return '<a href="/login">Login through GitLab</a>'


@app.route('/login')
def login():
    # URL для авторизации
    authorization_url = (
        f"{GITLAB_BASE_URL}/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=read_user"
    )
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    # Получение авторизационного кода из параметров
    code = request.args.get('code')
    if not code:
        return "Error: no authentication code."

    # Запрос на обмен кода на токен
    token_url = f"{GITLAB_BASE_URL}/oauth/token"
    response = requests.post(token_url, data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    })

    if response.status_code != 200:
        return f"Error while gerring token: {response.json()}"

    token_data = response.json()
    access_token = token_data['access_token']

    # Запрос информации о пользователе
    user_info_url = f"{GITLAB_BASE_URL}/api/v4/user"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_response = requests.get(user_info_url, headers=headers)

    if user_response.status_code != 200:
        return f"Error while getting user data: {user_response.json()}"

    user_data = user_response.json()
    session['user'] = user_data
    print(user_data)
    return f"Your are logged in as: {user_data['username']}"
    

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
