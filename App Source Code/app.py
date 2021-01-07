import os
from flask import Flask, session, request, redirect, render_template, jsonify, url_for
from flask_session import Session
import spotipy
import uuid
import pandas as pd
from rec_functions import get_artist_tracks, get_user_tracks, compare_songs, user_tracks_dataframe, get_playlist_embeddings, get_current_track_embed_link, album_art_url, parse_spotify_link, recommend_songs, playlist_url, make_playlist, one_click_rec, spotify_uri_search, artist_based_recs
from sklearn.metrics.pairwise import pairwise_distances, cosine_distances, cosine_similarity
pd.set_option("display.precision", 14)

CLIENT_ID='472796d4b7904eb8ab972808d46bd0b0'
CLIENT_SECRET='cc89036aabd04a61a9d20970a0510186'
REDIRECT_URI='https://alexaurusrecs.herokuapp.com/'
SCOPE = 'user-read-currently-playing playlist-modify-public user-top-read playlist-read-private'


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')


@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE,
                                               cache_path=session_cache_path(), 
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return render_template('sign_in.html', auth_url=auth_url)
       
    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return render_template('home.html', spotify=spotify)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/playlists')
def playlists():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    embed_links = get_playlist_embeddings(spotify)

    return render_template('playlist.html', embed_links=embed_links)          


@app.route('/currently_playing')
def currently_playing():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if track:
        res = f"You're listening to {track['item']['name']} by {track['item']['artists'][0]['name']}. Nice choice!"
        art_url = album_art_url(spotify, track['item']['uri'])
        return render_template('current_track.html', res=res, art_url=art_url)
    else:
        return render_template('no_current_track.html')


@app.route('/top_tracks')
def top_tracks():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    df = user_tracks_dataframe(spotify, limit=50)
    #html = df.to_html
    #return html
    return render_template('top_tracks.html', df=df)


@app.route('/song_based')
def song_based():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    genre_seeds = spotify.recommendation_genre_seeds()['genres']

    return render_template('song_based.html', genre_seeds=genre_seeds)

@app.route('/song_based_submit')
def song_based_submit():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    user_input = request.args
    uri = parse_spotify_link(user_input['link'])
    genre = user_input['selected_genre']
    if user_input['time_range']:
        listener_based = True
    else:
        listener_based = False
    
    time_range = user_input['time_range']
    n_tracks = int(user_input['n_tracks'])
    playlist_name = user_input['playlist_name']


    playlist_uris, history = recommend_songs(spotify, listener_based=listener_based, genres=[genre], tracks=[uri], n_tracks=n_tracks, user_time_range=time_range)
    
    if not history['listener_based']:
        response = 'Awesome!'
    elif history['no_listening_history']:
        response = "It looks like you have no listening history. Since we couldn\'t base our recs off your taste, we created a playlist of the artist top songs."
    elif history['insufficient_history']:
        response = f"You had insufficient {time_range.replace('_', ' ')} listening history. So we had to look into your others. We hope you don\'t mind"
    else:
        response = 'Awesome!'
    
    user = spotify.current_user()['id']
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=playlist_uris)
    # This function is not working for some reason. Take a look at it later!                                 
    #make_playlist(spotify, playlist_uris, playlist_name)
    url = playlist_url(playlist_id)

    return render_template('song_based_submit.html', playlist_name=playlist_name, url=url, response=response)


@app.route('/artist_based')
def artist_based():
    return render_template('artist_based.html')


@app.route('/artist_based_submit')
def artist_based_submit():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user = spotify.current_user()['id']

    user_input = request.args
    n_tracks = int(user_input['n_tracks'])
    playlist_name = user_input['playlist_name']
    artist_uri = parse_spotify_link(user_input['link'])
    time_range = user_input['time_range']

    playlist_uris, history = artist_based_recs(spotify, artists=[artist_uri], n_tracks=n_tracks, user_time_range=time_range)


    if history['no_listening_history']:
        response = "It looks like you have no listening history. Since we couldn\'t base our recs off your taste, we created a playlist of the artist top songs."
    elif history['insufficient_history']:
        response = f"You had insufficient {time_range.replace('_', ' ')} listening history. So we had to look into your others. We hope you don\'t mind"
    else:
        response = 'Awesome!'
    
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=playlist_uris)
    url = playlist_url(playlist_id)
    return render_template('artist_based_submit.html', playlist_name=playlist_name, url=url, response=response)
    

@app.route('/one_click_landing')
def one_click_landing():
    return render_template('one_click_landing.html')


@app.route('/one_click')
def one_click():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    playlist_name="Alexaurus Recs"
    playlist_uris, listening_history = one_click_rec(spotify)
    if not listening_history:
        response = "It looks like you have no listening history. Here are some editor's choices."
    else:
        response = "Awesome!"

    user = spotify.current_user()['id']
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=playlist_uris)
    
    url = playlist_url(playlist_id)
           
    return render_template('one_click_recommender.html', playlist_name=playlist_name, response=response, url=url)


@app.route('/spotify_code_search')
def spotify_code_search():
    return render_template('spotify_code_search.html')


@app.route('/spotify_code_search_results')
def spotify_code_search_result():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)

    user_input = request.args
    media_type = user_input['type']
    search = user_input['search']
    results = spotify_uri_search(spotify, search=search, type=media_type)
    columns = results.columns

    return render_template('spotify_code_search_results.html', results=results, columns=columns)




@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')





######DEPRICATED######
@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit')
def make_playlist():

    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user_input = request.args
    n_tracks = int(user_input['n_tracks'])
    playlist_name = user_input['playlist_name']
    uri = user_input['link'].split('/')[-1]
    track_name = spotify.track(uri)['name']
    user = spotify.current_user()['id']

    recs = spotify.recommendations(seed_tracks=[uri], limit=n_tracks)
    uris = [track['uri'] for track in recs['tracks']]
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=uris)
    return f'We just created a playlist called {playlist_name} based off of {track_name}. We added {n_tracks} tracks to {playlist_name}. Enjoy!'

@app.route('/artist_based_recommendations')
def artist_based_recommendations():
    return render_template('artist_based_recommendations.html')

@app.route('/submit_artist_based')
def submit_artist_based():
    auth_manager = spotipy.oauth2.SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=session_cache_path())
    if not auth_manager.get_cached_token():
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user = spotify.current_user()['id']

    user_input = request.args
    n_tracks = int(user_input['n_tracks'])
    playlist_name = user_input['playlist_name']
    artist_uri = user_input['uri']
    time_range = user_input['time_range']

    artist_df = get_artist_tracks(spotify, artists=[artist_uri])

    user_df = get_user_tracks(spotify, limit=n_tracks, time_range=time_range)

    playlist_uris = compare_songs(artist_df, user_df)
    
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=playlist_uris)
    return f'''
        <html>
            <p>
                We just created a playlist called {playlist_name} based off of your most listened to tracks!.<br>We added {len(playlist_uris)} tracks to {playlist_name}.<br>Enjoy!'
            </p>
            <p>
                <iframe src="https://open.spotify.com/follow/1/?uri={artist_uri}&size=detail&theme=light" width="300" height="56" scrolling="no" frameborder="0" style="border:none; overflow:hidden;" allowtransparency="true"></iframe>
            </p>
            <p>
                <iframe src="https://open.spotify.com/embed/playlist/{playlist_id}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
            </p>
        </html>
            '''



if __name__ == '__main__':
	app.run(threaded=True, debug=True)
