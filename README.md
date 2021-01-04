# Alexaurus Recs:
## A Spotify Recommendation Engine


<img src="./assets/noun_Dinosaur_3146844.png" alt="drawing" height ="300" width="300"/>



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

Can we improve upon Spotify's base recommendations by directly comparing recommended tracks' audio features with those of tracks from a user's most-frequent listening history?


## Executive Summary

Alexaurus Recs is an app that includes a suite of recommendation engines to hopes to improve upon Spotify's base recommendations and users visualize their personal data collected by Spotify. The app uses a Flask web-app framework and is deployed on heroku. See the source code [here](https://github.com/alexfioto/Spotify-Recommender/tree/main/App%20Source%20Code).







## Conclusion

Accuracy will be used as the metric to determine best model since this project simply aims to correctly classify subreddits rather than optimize for precision or recall. 

Between the two models, I found that the Random Forest Classifier performed best. Both models seem to misclassify Machine Learning posts as AI posts more frequently than the opposite. 

These are the features (or words) that had the most impact on the performance model in order of importance:


|Feature Name|
|------|
|removed|
|ai|
|artificial|
|intelligence|
|learning|
|machine|
|model|

I found that the word "removed" was found more frequently in the Artifical Intelligence subreddit indicating that more users removed posts than in the Machine Learning subreddit. 

I also discovered that lemmatizing the text produced better results than stemming or no preprocessing. 

This classification problem was relatively difficult as the two topics are very similar and use much of the same vocabulary. It seemed that both of my models seemed to perform better with more information. The more I suppressed the data input the worse the model performed.

Looking forward, I hope to continue to hone NLP preprocessing skills to achieve higher accuracy scores. 

### Additional Classifiers

I ended up trying HistGradientBoost, AdaBoost and SVC and Gradient Boost Classifiers. None of these worked well out of the box. I found that a basic Logistic Regression worked almost as well as my best Random Forest Classifier. 

Thank you for your interest!


## Data Dictionary

|Feature|Type|Dataset|Description|
|---|---|---|---|
|**title**|*string*|processed_posts|Title of the subreddit|
|**subreddit**|*int*|processed_posts|Binary. Machine Learning: 1, Artificial Intelligence: 0|
|**selftext**|*string*|processed_posts|Text of the post|
|**permalink**|*string*|processed_posts|Link to post|
|**author**|*string*|processed_posts|Author of post|
|**created_utc**|*int*|processed_posts|Epoch time of post creation|
|**media_only**|*boolean*|processed_posts|True if post is only media|
|**all_text**|*string*|processed_posts|Combined title and selftext|
|**stem_all_text**|*string*|processed_posts|Stemmed all_text|
|**lem_all_text**|*string*|processed_posts|Lemmatized all_text|
