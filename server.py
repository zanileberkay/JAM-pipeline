from flask import Flask, request, jsonify, redirect, session, url_for
import os
import requests
from dotenv import load_dotenv
import logging
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize Firebase Admin
cred = credentials.Certificate('path_to_your_service_account_key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/authorize', methods=['GET'])
def authorize():
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        'response_type': 'code',
        'redirect_uri': os.getenv('REDIRECT_URI'),
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'scope': 'user-read-private user-read-email',
    }
    query = '&'.join([f'{k}={v}' for k, v in params.items()])
    full_url = f"{auth_url}?{query}"
    return redirect(full_url)

@app.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400
    token = get_spotify_token(code)
    if token:
        session['spotify_token'] = token
        return redirect(url_for('signup'))
    else:
        return "Error obtaining token", 500

def get_spotify_token(code):
    url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('REDIRECT_URI'),
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if 'spotify_token' in session:
        # Add user profile data to Firestore
        user_ref = db.collection('users').document(data['email'])
        user_ref.set({
            'name': data['name'],
            'nickname': data['nickname'],
            'email': data['email'],
            'biography': data['biography'],
            'dob': data['dob'],
            'gender': data['gender'],
            'spotify_token': session['spotify_token']
        })
        return jsonify({"status": "success"}), 200
    return jsonify({"error": "Authorization required"}), 401

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
