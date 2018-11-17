import json
import os
from flask import Flask, session, redirect, request, url_for, jsonify, render_template
from requests_oauthlib import OAuth2Session

OAUTH2_CLIENT_ID = "498036184501714944"
OAUTH2_CLIENT_SECRET = "q8nOQLkd-jdKJUVC2jonYLitYsDOADiL"
OAUTH2_REDIRECT_URI = 'https://rathumakara.iconicto.com/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__)
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/auth/')
def auth():
    scope = request.args.get(
        'scope',
        'identify email connections guilds guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@app.route('/callback/')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('.me'))


@app.route('/me/')
def me():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
    return jsonify(user=user, guilds=guilds, connections=connections)


@app.route('/player_status/', methods=["GET"])
def get_player_status():
    try:
        with open('/root/RathuMakaraFM-DiscordBot/status.json') as f:
            data = json.load(f)

        return jsonify(data)
    except Exception as e:
        return jsonify(
            {
                "now_playing": {"song": None, "uploader": None, "thumbnail": None, "url": None,
                                "duration": None, "progress": None, "extractor": None, "requester": None,
                                "is_pause": False},
                'queue': [],
                "is_pause": False,
                "auto_play": False
            }
        )


if __name__ == '__main__':
    app.run()
