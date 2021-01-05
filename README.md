# Alexaurus Recs
### A Spotify Recommendation Engine


<img src="./assets/noun_Dinosaur_3146844.png" alt="green dinosaur" height ="300" width="300"/>



## Introduction
Alexaurus Recs aims to improve on Spotify's recommendation engine by directly comparing user data to base Spotify song recommendations. [Try the app here](https://alexaurusrecs.herokuapp.com/)
<br>
**Note:** You will need a Spotify account to use the app. 


I utilize the following python libaries:

- **spotipy**: Python wrapper for Spotify API
- **flask**: Web-app framework
- **numpy**: scientific computing
- **pandas**: data importing, cleaning, and exploratory analysis
- **scikit-learn**: machine learning


## Problem Statement

Can we improve upon Spotify's basic song recommendations by utilizing a tracks' raw audio feature data and a user's listening history?


## Executive Summary

Alexaurus Recs is an app that includes a suite of recommendation engines with hopes to improve upon Spotify's base recommendations and facilitate a way for users visualize their personal data collected by Spotify. The app uses a Flask web-app framework and is deployed on heroku. See the source code [here](https://github.com/alexfioto/Spotify-Recommender/tree/main/App%20Source%20Code). My recommenders pairwise compare (using cosine distance) the audio features of  Spotify's basic song recommendations with the audio features of a user's most-listened-to tracks. 

Albeit subjective, my recommenders have performed significantly better than the basic Spotify recommendations. 


## Notebooks
I have included two Jupyter notebooks in this repository that follow my train of thought while creating the app. 

#### Recommenders.ipynb 
Details the recommender functions that are deployed Heroku. 

#### App_utilities.ipynb
Explains details about the functions that serve as utilities within the app. This includeds functions to search for Spotify URIs, to list a user's top tracks, display playlists and a few others.

## Source Code
The source code is static and is updated every few weeks.


## Audio Features Data Dictionary

|Feature|Type|Description|
|---|---|---|
|**danceability**|*float*|Describes how suitable a track is for dancing|
|**energy**|*float*|Measure that represents a perceptual measure of intensity and activity|
|**key**|*int*|Estimated overall key|
|**loudness**|*float*|Overall loudness of a track in decibels|
|**mode**|*int*|Modality: major or minor|
|**speechiness**|*float*|Detects the presence of spoken words in track|
|**acousticness**|*float*|Confidence measure whether the track is acoustic|
|**instrumentalness**|*float*|Predicts whether a track contains no vocals. Above .5 intended to represent instrumental|
|**valence**|*float*|Describes the musical positiveness conveyed by a track|
|**liveness**|*float*|Detects the presence of an audience in the recording|
|**tempo**|*float*|Overall estimated tempo of a track in beats per minute (BPM)|

