from sklearn.metrics.pairwise import pairwise_distances, cosine_distances, cosine_similarity
pd.set_option("display.precision", 14)

def get_artist_tracks(sp, artists, n_albums=100,):
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
        albums = sp.artist_albums(artist)
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



    def get_user_tracks(sp, limit=10):
    user_tracks = sp.current_user_top_tracks(limit=limit)
    audio_features =  sp.audio_features([item['uri'] for item in user_tracks['items']])
    names = [item['name'] for item in user_tracks['items']]
    df = pd.DataFrame.from_dict(audio_features)
    df['track_name'] = names
    return df


    def compare_songs(df, user_df):
    
    band_track_names = df['track_name']
    user_track_names = user_df['track_name']

    df_numeric = df.loc[:, df.columns[:11]]
    user_df_numeric = user_df.loc[:, user_df.columns[:11]]
    
    recs = pairwise_distances(df_numeric, user_df_numeric, metric='cosine')
    rec_df = pd.DataFrame(recs, columns=user_track_names, index=band_track_names)    
    rec_df = 1 - rec_df
    rec_df.drop_duplicates(inplace=True)
    
    song_list = []
    
    for user_track in new_rec_df.columns:
        max_cosine = new_rec_df[user_track].max()
        song_name = new_rec_df[new_rec_df[user_track] == max_cosine].index[0]
        song_uri = list(df.loc[df['track_name'] == song_name, 'uri'])[0]
        print(f'{user_track}------ closest to ---------> {song_name}')
        song_list.append((song_name, song_uri))
    
    return song_list

def get_current_track_embedding(spotify):
    track = spotify.current_user_playing_track()
    uri = track['item']['uri'].replace('spotify:track:', '')
    code = '<iframe src="https://open.spotify.com/embed/track/###" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
    code_uri = code.replace('###', uri)
    return code_uri

