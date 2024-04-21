from flask import Flask, request, jsonify, redirect, session, url_for
import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()  # Load environment variables from .env file
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route('/authorize', methods=['GET'])
def authorize():
    """ Redirects the user to Spotify's authorization page. """
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
    """ Handles the callback after Spotify redirects back with a code. """
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
    """ Exchanges the authorization code for an access token from Spotify. """
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

@app.route('/signup', methods=['GET'])
def signup():
    """ Shows the signup page only if the user has a valid token stored in session. """
    if 'spotify_token' in session:
        return 'Sign Up Page Content Here'
    return redirect(url_for('authorize'))

if __name__ == '__main__':
    app.run(debug=True)
