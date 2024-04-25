from flask import Flask, request, jsonify, redirect, session, url_for
import os
import requests
import logging
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize Firebase Admin
cred_path = 'path_to_your_service_account_key.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/authorize', methods=['GET'])
def authorize():
    """ Redirect to Spotify for user authorization. """
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        'response_type': 'code',
        'redirect_uri': os.getenv('REDIRECT_URI'),
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'scope': 'user-read-private user-read-email',
    }
    query = '&'.join([f'{k}={v}' for k, v in params.items()])
    full_url = f"{auth_url}?{query}"
    logging.info(f"Redirecting to Spotify for authorization: {full_url}")
    return redirect(full_url)

@app.route('/callback', methods=['GET'])
def callback():
    """ Handle the callback from Spotify with the authorization code. """
    code = request.args.get('code')
    if not code:
        logging.error("No authorization code provided.")
        return "Error: No code provided", 400
    token = get_spotify_token(code)
    if token:
        session['spotify_token'] = token
        logging.info("Token received and stored in session.")
        return redirect(url_for('signup'))
    else:
        logging.error("Failed to obtain Spotify token.")
        return "Error obtaining token", 500

def get_spotify_token(code):
    """ Exchange the authorization code for an access token. """
    logging.info("Requesting Spotify token.")
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
        logging.info("Successfully received Spotify token.")
        return response.json().get('access_token')
    else:
        logging.error(f"Failed to get token: {response.text}")
        return None

@app.route('/signup', methods=['POST'])
def signup():
    """ Register or update user profile in Firestore after successful Spotify authorization. """
    if 'spotify_token' not in session:
        logging.warning("Unauthorized access attempt to signup.")
        return jsonify({"error": "Authorization required"}), 401

    data = request.json
    logging.info(f"Registering or updating user: {data['email']}")
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
    logging.info(f"User {data['email']} registered/updated successfully.")
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)  # Set debug to False for production environments
