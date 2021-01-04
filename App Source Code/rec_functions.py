from sklearn.metrics.pairwise import pairwise_distances, cosine_distances, cosine_similarity
import pandas as pd
pd.set_option("display.precision", 14)



def get_artist_tracks(sp, artists, n_albums=50):
    '''
    Function takes in the Spotify URI of one or more artists and returns a Pandas dataframe with Spotify's proprietary audio features.
    
    n_albums: number of albums to fetch per artist
    '''
    
    uris = []
    album_uris = []
    df_list = []
    
    # Checking if user input artists as a list. 
    if type(artists) != list:
        # Rectifying if user did not input list
        artists = [artists]
    
    for artist in artists:
        albums = sp.artist_albums(artist, limit=n_albums)
        for album in albums['items']:
            album_uris.append(album['uri'])
    
    for uri in album_uris:
        album = sp.album(uri)
        album_name = album['name']
        
        album_artist = ', '.join([artist['name'] for artist in album['artists']])
        
        tracks = sp.album_tracks(uri)
        audio_features_dict = sp.audio_features()
        df = pd.DataFrame.from_dict(tracks['items'])
        audio_features_df = pd.DataFrame.from_dict(sp.audio_features(list(df['uri'])))
        audio_features_df['track_name'] = df['name']
        audio_features_df['album_name'] = album_name
        audio_features_df['artist_name'] = album_artist
        df_list.append(audio_features_df)
    
    df = pd.concat(df_list)
    df.reset_index(inplace=True, drop=True)
    df.drop_duplicates()
    return df



def get_user_tracks(sp, limit=10, time_range='medium_term'):
    user_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    audio_features =  sp.audio_features([item['uri'] for item in user_tracks['items']])
    names = [item['name'] for item in user_tracks['items']]
    df = pd.DataFrame.from_dict(audio_features)
    df['track_name'] = names
    return df

def user_tracks_dataframe(spotify, limit=10):
    terms = ['short_term', 'medium_term', 'long_term']
    df_list = []
    for term in terms:
        tracks = spotify.current_user_top_tracks(limit=limit, time_range=term)
        track_names = [track['name'] for track in tracks['items']]
        artist_list = []
        for track in tracks['items']:
            artists = ', '.join([artist['name'] for artist in track['artists']])
            artist_list.append(artists)
        df = pd.DataFrame(list(zip(track_names, artist_list)), 
                          columns = ['track_name', 'artist_name'])
        df['time_range'] = term
        df_list.append(df)
    df = pd.concat(df_list)
    df.reset_index(inplace=True, drop=True)
    return df


def compare_songs(artist_df, user_df):
    '''
    Takes in a dataframe of artist tracks and audio feautes, and a dataframe of user top tracks. 
    Returns tracks in artist_df that are most alligned with user tracks.
    '''
    
    band_track_names = artist_df['track_name']
    user_track_names = user_df['track_name']
    
    df_numeric = artist_df.loc[:, artist_df.columns[:11]]
    user_df_numeric = user_df.loc[:, user_df.columns[:11]]
    
    recs = pairwise_distances(df_numeric, user_df_numeric, metric='cosine')
    rec_df = pd.DataFrame(recs, columns=user_track_names, index=band_track_names)    
    rec_df = 1 - rec_df
    rec_df.drop_duplicates(inplace=True)
    
    song_list = []
    
    for user_track in rec_df.columns:
        max_cosine = rec_df[user_track].max()
        song_name = rec_df[rec_df[user_track] == max_cosine].index[0]
        song_uri = list(artist_df.loc[artist_df['track_name'] == song_name, 'uri'])[0]
        #print(f'{user_track}------ closest to ---------> {song_name}')
        song_list.append((song_name, song_uri))
        
    uri_list = []
    [uri_list.append(track[1]) for track in song_list if track[1] not in uri_list]
    
    return uri_list

# Depricated 
# def get_playlist_embeddings(spotify):
#     '''
#     Takes in user authentication object and returns HTML embedding codes for user playlists
#     '''
#     playlists = spotify.current_user_playlists()
#     playlist_ids = [playlist['id'] for playlist in playlists['items']]
#     embed_code = '<iframe src="https://open.spotify.com/embed/playlist/####" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
#     codes = ' '.join([embed_code.replace('####', playlist_id) for playlist_id in playlist_ids])
#     return codes

def get_playlist_embeddings(spotify):
    '''
    Takes in user authentication object and returns HTML embedding codes for user playlists
    '''
    playlists = spotify.current_user_playlists()
    playlist_ids = [playlist['id'] for playlist in playlists['items']]
    embed_link = "https://open.spotify.com/embed/playlist/####"
    codes = [embed_link.replace('####', playlist_id) for playlist_id in playlist_ids]
    return codes


def get_current_track_embed_link(spotify):
    link = sp.current_user_playing_track()['item']['external_urls']['spotify']
    return link.replace('https://open.spotify.com', 'https://open.spotify.com/embed')

def album_art_url(spotify, track_uri):
    '''
    Retrieves album art url
    
    Parameters:
    spotify: user authentication token
    uri: Spotify track URI
    '''
    
    # Getting track object
    track = spotify.track(track_uri)
    
    # Extracting image URL 
    url = track['album']['images'][0]['url']
    
    return url

def parse_spotify_link(link):
    if '?' in link:
        return link.split('/')[-1].split('?')[0]
    else:
        return link.split('/')[-1]

def recommend_songs(spotify, artists=None, genres=None, tracks=None, limit=100, n_tracks=10, listener_based=True, time_range='medium_term', drop_cols=[]):
    '''
    This function will recommend songs based on a seed artist, seed genres and/or seed tracks.
    The searched songs will be compared to user top tracks and return only those songs with the 
    highest cosine similarity.
   
    Parameters:
    
    drop_cols: columns to drop from numeric featue comparison. Choose from: danceability
                                                                            energy
                                                                            key
                                                                            loudness
                                                                            mode
                                                                            speechiness
                                                                            acousticness
                                                                            instrumentalness
                                                                            liveness
                                                                            valence
                                                                            tempo
    '''
    
    # Fetching Spotify recommendations 
    recs = spotify.recommendations(seed_artists=artists, seed_genres=genres, seed_tracks=tracks, limit=limit)
    
    # Saving lists of track names and URIs of recommended tracks
    rec_track_names = [track['name'] for track in recs['tracks']]
    uris = [track['uri'] for track in recs['tracks']]
    
    # Creating audio features dataframe of recommended tracks
    rec_df = pd.DataFrame.from_dict(spotify.audio_features(uris))
    rec_df['track_name'] = rec_track_names
    rec_df['uri'] = uris
    
    # If not listener based, returning list of URIs for Spotify recommended songs
    if not listener_based:
        return list(rec_df[:n_tracks]['uri'])
    
    else: # If listener based
        
        # Fetching user top tracks
        user_tracks = spotify.current_user_top_tracks(limit=n_tracks, time_range=time_range)
        
        # Saving lists of track names and URIs of user top tracks
        user_track_names = [track['name'] for track in user_tracks['items']]
        uris = [track['uri'] for track in user_tracks['items']]
        
        # Creating audio features dataframe of user top_tracks
        user_df = pd.DataFrame.from_dict(spotify.audio_features(uris))
        user_df['track_name'] = user_track_names
        user_df['uri'] = uris
        
        # Setting new dataframes of only numeric features to be compared
        rec_df_numeric = rec_df.loc[:, rec_df.columns[:11]]
        user_df_numeric = user_df.loc[:, user_df.columns[:11]]
        
        # If drop_cols, dropping appropriate columns from each numeric dataframe
        if drop_cols:
            rec_df_numeric.drop(drop_cols, inplace=True, axis=1)
            user_df_numeric.drop(drop_cols, inplace=True, axis=1)
              
        
        comps = pairwise_distances(rec_df_numeric, user_df_numeric, metric='cosine')
        comps_df = pd.DataFrame(comps, columns=user_track_names, index=rec_track_names)
        comps_df = 1 - comps_df
        comps_df.drop_duplicates(inplace=True)
        
        song_list = []
    
        for user_track in comps_df.columns:
            max_cosine = comps_df[user_track].max()
            song_name = comps_df[comps_df[user_track] == max_cosine].index[0]
            song_uri = list(rec_df.loc[rec_df['track_name'] == song_name, 'uri'])[0]
            #print(f'{user_track}------ closest to ---------> {song_name}')
            song_list.append((song_name, song_uri))

        uri_list = []
        [uri_list.append(track[1]) for track in song_list if track[1] not in uri_list]
    
    
        return uri_list

def make_playlist(spotify, playlist_uris, playlist_name):
    user = spotify.current_user()['id']
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=playlist_uris)
def playlist_url(playlist_id):
    return "https://open.spotify.com/embed/playlist/" + playlist_id

def one_click_rec(spotify):
    uris = [uri['uri'] for uri in spotify.current_user_top_tracks(limit=5)['items']]
    recs = spotify.recommendations(seed_artists=None, seed_genres=None, seed_tracks=uris, limit=20)
    rec_uris = [uri['uri'] for uri in recs['tracks']]
    return rec_uris

# def one_click_rec(spotify):
#     try:
#         uris = [uri['uri'] for uri in spotify.current_user_top_tracks(limit=55352345435234523453)['items']]
#     except:
#         playlist_id = spotify.featured_playlists(limit=1)['playlists']['items'][0]['id']
#         playlist = spotify.playlist(playlist_id, additional_types=('track', ))
#         uris = [uri['track']['uri'] for uri in playlist['tracks']['items'][:5]]
#     recs = spotify.recommendations(seed_artists=None, seed_genres=None, seed_tracks=uris, limit=20)
#     rec_uris = [uri['uri'] for uri in recs['tracks']]
#     return rec_uris, uris

def spotify_uri_search(spotify, search, type='album', limit=10):
    '''
    Search for a Spotify track, album, playlist, show or episode URI. 
    
    Parameters:
    search: search string
    
    type: type of uri. Choose from track, album, playlist, artist, show or episode URI. 
    
    limit: integer limit to return. 0-50
    '''
    # Creating empty results list and results dictionary
    if limit > 50 or limit < 1:
        raise TypeError('Limit needs to be an integer between 1-50')
    results = []
    res_dict = {}

     # Replacing spaces with + 
    q = search.replace(' ', '+')

    # Creating search object
    res = spotify.search(q=q, limit=limit, type=type,)

    # Selecting all of the tracks in search object
    items = res[type+'s']['items']
    
    # Iterating through tracks or albums 
    for item in items:
        # Creating result dictionary entry
        res_dict[item['name']] = item['uri']
        
#         # Adding name of track or album along with the artists to results
#         results.append(item['name'] + ' BY ' + item['artists'][0]['name'])
    
#     # Printing results for user to decide which album
#     for i in range(len(results)):
#         print(f'{i}: {type}: {results[i]}')
        
#     # Requesting user input for correct choice
#     response = input('Please select a valid index')
    
#     # Selecting appropriate Spotify URI
#     uri = res_dict.get(results[int(response)].split(' BY ')[0])
    
    return res_dict