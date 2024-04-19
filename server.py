from flask import Flask, request, jsonify, redirect, session, url_for
import os
import requests
from google.cloud import firestore
from dotenv import load_dotenv
import logging

# Set up basic configuration for logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()  # Loads environment variables from .env file

app = Flask(__name__)  # Ensure app is defined before any use
app.config['SECRET_KEY'] = 'your_secret_key'

db = firestore.Client()

@app.route('/')
def home():
    logging.info("Visited home page")
    return 'Welcome to the Spotify Auth Service! This is the landing page.'

@app.route('/authorize', methods=['GET'])
def authorize():
    try:
        auth_url = "https://accounts.spotify.com/authorize"
        params = {
            'response_type': 'code',
            'redirect_uri': os.getenv('REDIRECT_URI'),
            'scope': 'user-read-private user-read-email',
            'client_id': os.getenv('SPOTIFY_CLIENT_ID')
        }
        query = '&'.join([f'{k}={v}' for k, v in params.items()])
        full_url = f"{auth_url}?{query}"
        logging.info(f"Redirecting to Spotify authorization URL: {full_url}")
        return redirect(full_url)
    except Exception as e:
        logging.error(f"Error in authorize: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    code = request.args.get('code')
    if not code:
        logging.warning("No code provided in callback")
        return "Error: No code provided", 400
    try:
        token = get_spotify_token(code)
        if token:
            session['spotify_token'] = token
            logging.info("Token stored in session and redirecting to complete registration")
            return redirect(url_for('complete_registration'))
        else:
            logging.error("Failed to retrieve token")
            return "Error obtaining token", 500
    except Exception as e:
        logging.error(f"Exception in callback: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

def get_spotify_token(code):
    try:
        url = "https://accounts.spotify.com/api/token"
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': os.getenv('REDIRECT_URI'),
            'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
            'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET')
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logging.error(f"Failed to exchange code for token: {response.text}")
            return None
    except Exception as e:
        logging.error(f"Exception in get_spotify_token: {str(e)}")
        return None

@app.route('/complete_registration', methods=['POST'])
def complete_registration():
    data = request.json or {}
    try:
        doc_ref = db.collection(u'users').document(data.get('username'))
        doc_ref.set({
            'username': data.get('username'),
            'email': data.get('email'),
            'bio': data.get('bio'),
            'gender': data.get('gender'),
            'birthday': data.get('birthday'),
            'spotify_token': session.get('spotify_token', '')
        })
        logging.info("User registration completed successfully")
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        logging.error(f"Error in complete_registration: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))#
