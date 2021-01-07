from sklearn.metrics.pairwise import pairwise_distances, cosine_distances, cosine_similarity
import pandas as pd
pd.set_option("display.precision", 14)



def artist_based_recs(spotify, artists, n_tracks=15, user_time_range='medium_term'):
    '''
    Combo function
    '''
    
    ########### ARTIST TRACKS ###########

    uris = []
    album_uris = []
    df_list = []
    artist_names = []
    
    # Checking if user input artists as a list. 
    if type(artists) != list:
        # Rectifying if user did not input list
        artists = [artists]
    
    # Iterate through artists
    for artist in artists:
        artist_names.append(spotify.artist(artist)['name'])
        # Fetches the albums JSONs
        albums = spotify.artist_albums(artist, limit=25)
        # Iterating through the albums and appending the artist URIs
        for album in albums['items']:
            album_uris.append(album['uri'])
    
    # Iterate through the album URIs
    for uri in album_uris:
        # Fetching album JSON
        album = spotify.album(uri)
        # Fetching album name
        album_name = album['name']
        # Fetching all artists on album
        album_artist = ', '.join([artist['name'] for artist in album['artists']])
            
        # Fetching all of the track URIs on the album
        tracks = spotify.album_tracks(uri)
        # Listing track URIs and names
        track_uris = [track['uri'] for track in tracks['items']]
        track_names = [track['name'] for track in tracks['items']]
        
        # Fetching audio features from the track URIs and assigning track name, album name and album artist
        try:
            audio_features_df = pd.DataFrame.from_dict(spotify.audio_features(track_uris))
            audio_features_df['track_name'] = track_names
            audio_features_df['album_name'] = album_name
            audio_features_df['artist_name'] = album_artist
        except:
            pass
        
        # Appending dataframe to list to concatenate
        df_list.append(audio_features_df)
    
    # Concatenating dataframes, resetting index and dropping duplicates
    artist_df = pd.concat(df_list)
    artist_df.reset_index(inplace=True, drop=True)
    artist_df.drop_duplicates()
    
    # This is a string that will be used in our filter that includes only rows that have 1 or more of the artists in the listed artists
    filter_artists = '|'.join(artist_names)
    # Filtering our dataframe using our string
    artist_df = artist_df[artist_df['artist_name'].str.contains(filter_artists)]
    
    ########### USER TRACKS ###########
    
    time_ranges = ['short_term', 'medium_term', 'long_term']
    time_ranges.remove(user_time_range)
    
    items = spotify.current_user_top_tracks(limit=n_tracks, time_range=user_time_range)

    
    user_uris = [item['uri'] for item in items['items']]
    names = [item['name'] for item in items['items']]

    history = {'no_listening_history': False, 'insufficient_history':False}
    
    for time_range in time_ranges:
        
        if len(user_uris) >= n_tracks:
            break
        items = spotify.current_user_top_tracks(limit=n_tracks, time_range=time_range)
        
        user_uris += [item['uri'] for item in items['items']]
        extra_names = [item['name'] for item in items['items']]
        names += extra_names
        history['insufficient_history'] = True
   
    
    if len(user_uris) == 0:
        uris = []
        history['no_listening_history'] = True
        for artist in artists:
            for track in spotify.artist_top_tracks(artist)['tracks']:
                uris.append(track['uri'])
        return (uris, history)
    
    elif len(user_uris) > 0 and len(user_uris) < n_tracks:
        pass  
    
    else:  
        user_uris[:n_tracks]
        names[:n_tracks]
        
    
    audio_features =  spotify.audio_features(user_uris)

    user_df = pd.DataFrame.from_dict(audio_features)
    
    # Setting track names
    user_df['track_name'] = names
    
    ########### COMPARE TRACKS ###########

    artist_track_names = artist_df['track_name']
    user_track_names = user_df['track_name']
    
    artist_df_numeric = artist_df.loc[:, artist_df.columns[:11]]
    user_df_numeric = user_df.loc[:, user_df.columns[:11]]
    
    recs = pairwise_distances(artist_df_numeric, user_df_numeric, metric='cosine')
    rec_df = pd.DataFrame(recs, columns=user_track_names, index=artist_track_names)    
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
    
    return uri_list, history


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


def recommend_songs(spotify, artists=None, genres=None, tracks=None, limit=100, n_tracks=10, listener_based=True, user_time_range='medium_term', drop_cols=[]):
    '''
    This function will recommend songs based on a seed artist, seed genres and/or seed tracks.
    The searched songs will be compared to user top tracks and return only those songs with the 
    highest cosine similarity.
   
    Parameters:
    
    spotify: OAuth user instance
    
    artists: list of Spotify artist URIs
    
    genres: list of seed genres
    
    tracks: list of Spotify track URIs
    
    limit: number of basic Spotify recommendations for comparison
    
    n_tracks: number of tracks to pull from user listening history
    
    listener_based: boolean, if True, function will pull user data and compare to base recommendations. If False, function will return n_tracks of base recommendations
    
    time_range: the listening history time range to pull from user listening data
    
    drop_cols: columns to drop from numeric featue comparison. 
    Choose from:    danceability
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
    # Instantiating history
    history = {'no_listening_history': False, 'insufficient_history':False, 'listener_based':listener_based}

    
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
        return (list(rec_df[:n_tracks]['uri']), history)
    
    else: # If listener based
        time_ranges = ['short_term', 'medium_term', 'long_term']
        time_ranges.remove(user_time_range)

        items = spotify.current_user_top_tracks(limit=n_tracks, time_range=user_time_range)


        user_uris = [item['uri'] for item in items['items']]
        user_track_names = [item['name'] for item in items['items']]


        for time_range in time_ranges:

            if len(user_uris) >= n_tracks:
                break
            items = spotify.current_user_top_tracks(limit=n_tracks, time_range=time_range)

            user_uris += [item['uri'] for item in items['items']]
            extra_names = [item['name'] for item in items['items']]
            user_track_names += extra_names
            history['insufficient_history'] = True


        if len(user_uris) == 0:
            history['no_listening_history'] = True
            return (list(rec_df[:n_tracks]['uri']), history)


        elif len(user_uris) > 0 and len(user_uris) < n_tracks:
            pass  

        else:  
            user_uris[:n_tracks]
            user_track_names[:n_tracks]

        
        # Creating audio features dataframe of user top_tracks
        user_df = pd.DataFrame.from_dict(spotify.audio_features(user_uris))
        user_df['track_name'] = user_track_names
        user_df['uri'] = user_uris
        
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
    
    
        return uri_list, history


def make_playlist(spotify, playlist_uris, playlist_name):
    user = spotify.current_user()['id']
    playlist = spotify.user_playlist_create(user=user, name=playlist_name, public=True)
    playlist_id = playlist['id']
    spotify.user_playlist_add_tracks(user=user,
                                     playlist_id=playlist_id,
                                     tracks=playlist_uris)
def playlist_url(playlist_id):
    return "https://open.spotify.com/embed/playlist/" + playlist_id

# def one_click_rec(spotify):
#     uris = [uri['uri'] for uri in spotify.current_user_top_tracks(limit=5)['items']]
#     recs = spotify.recommendations(seed_artists=None, seed_genres=None, seed_tracks=uris, limit=20)
#     rec_uris = [uri['uri'] for uri in recs['tracks']]
#     return rec_uris

def one_click_rec(spotify):
    '''
    Create a basic recommended Spotify playlist based on your listening history.
    If listening history is not deep enough, base playlist off of current Spotify Editor's recommended playlist.
    Returns a list of spotify URI codes of recommended songs
    
    Parameters:
        
        spotify: OAuth user authentication object
        
        limit: number of tracks to pull from listening history
        
    Returns:
        
        List of Spotify URI codes
        
    '''
    time_ranges = ['short_term', 'medium_term', 'long_term']
    listening_history=True
    uris = []
    for time_range in time_ranges:
        uris += [uri['uri'] for uri in spotify.current_user_top_tracks(limit=5, time_range=time_range)['items']]
    
    # In the case of no user listening history, we will return 
    if not uris:
        playlist_id = spotify.featured_playlists(limit=1)['playlists']['items'][0]['id']
        playlist = spotify.playlist(playlist_id, additional_types=('track', ))
        uris = [uri['track']['uri'] for uri in playlist['tracks']['items'][:5]]
        listening_history=False

    if len(uris) > 5:
        uris = uris[:5]
        
    # Request 20 recommended songs for the URIs designated above
    recs = spotify.recommendations(seed_tracks=uris, limit=20)
    rec_uris = [uri['uri'] for uri in recs['tracks']]
    return (rec_uris, listening_history)



def spotify_uri_search(spotify, search, type='album'):
    '''
    Search for a Spotify track, album, playlist, show or episode URI. 
    
    Parameters:
    search: search string
    
    type: type of uri. Choose from track, album, playlist, artist, show or episode URI. 
    
    '''
    # Creating empty results list and results dictionary
    results = []
    res_dict = {}

     # Replacing spaces with + 
    q = search.replace(' ', '+')

    # Creating search object
    res = spotify.search(q=q, limit=10, type=type,)

    # Selecting all of the tracks in search object
    items = res[type+'s']['items']
    
    if type == 'track':
        df = pd.DataFrame(columns=['Track', 'Artist', 'Code'])
        for i in range(len(items)):
            artists = ', '.join([artist['name'] for artist in items[i]['artists']])

            df.loc[i] = [items[i]['name'], artists, items[i]['uri']]
    
    elif type == 'playlist':
        df = pd.DataFrame(columns=['Playlist', 'Description', 'Code'])
        for i in range(len(items)):
            df.loc[i] = [items[i]['name'], items[i]['description'], items[i]['uri']]
    
    elif type == 'album':
        df = pd.DataFrame(columns=['Album', 'Artist', 'Code'])
        for i in range(len(items)):
            artists = ', '.join([artist['name'] for artist in items[i]['artists']])
            df.loc[i] = [items[i]['name'], artists, items[i]['uri']]
    
    else: # type == 'artist'
        df = pd.DataFrame(columns=['Artist', 'Followers', 'Code'])
        for i in range(len(items)):
            df.loc[i] = [items[i]['name'], items[i]['followers']['total'], items[i]['uri']]
    
    return df














    ####DEPRICATED####

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