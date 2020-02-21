from sklearn.ensemble import RandomForestClassifier  
import sklearn as sk 
import re
import nltk
from sklearn.feature_extraction.text import *
import pandas as pd
import numpy as np
import pickle
from collections import Counter


'''
    the train dataset was created from the following lines of code:

        ****
        Note please dont run this or it will 
        override the tweets i manually evaluated
        ****
    
    sample = tweets.sample(frac=1/20,random_state=3)
    sample.to_excel('train_tweets.xlsx')

    in excel I added a column for target. and that is waht I use as the training dataset below
'''

def download_data():
    train = pd.read_excel('./train_tweets.xlsx') # this is a dataframe of tweet objects, although i will only use the 'text' field for classificationn
    target = train['Target'] # these are the manual classifications i made
    # train.drop(['Target','contributors','favorited','id','id_str','retweeted','coordinates','created_at','geo'], inplace=True, axis=1)

    test = pd.read_pickle('./main_user_tweets.pkl') # a dataframe of tweet objects, I use the 'text' field for testing the classifier

    return train, target, test 


def predict(train, target, test):
    t = [i for i in train['text'].tolist()] # list of tweets from train
    t1 = [i for i in test['text'].tolist()] # list of tweets from test
    tweet_sum = t + t1 # a list of all tweets to use for creating a feauture matrix

    ########## The next 6 lines are the actual 6 lines of code to train the model and predict the test tweets

    tfidf_vectorizer = TfidfVectorizer(min_df=2) 
    X_tfidf = tfidf_vectorizer.fit_transform(tweet_sum) #creating feature matrix for entire vocab

    train_df = pd.DataFrame(X_tfidf.todense()).iloc[:415] # train feature matrix
    test_df  = pd.DataFrame(X_tfidf.todense()).iloc[415:] # test feature matrix

    RF = RandomForestClassifier(n_estimators=100, max_depth=40, random_state=0).fit(train_df, target) # create the classifier, using the train_df and the target values I entered
    predictions = RF.predict(test_df)  # predict tweet classification
    
    return predictions


def print_pred(predictions): # this is all just for printing... fluff 
    counter = Counter(predictions)
    print('Number of non-subject tweets: {0}'.format(counter[2]))
    print('Number of Technology focussed tweets: {0}'.format(counter[1]))
    print('Number of Trading focussed tweets: {0}'.format(counter[0]))


def print_examples(predictions,test): # this is also just for printing... fluff
    n=False
    tech=False
    trade=False
    for i,v in enumerate(list(predictions)):
        if i > 22:        
            if predictions[i] == 0 and trade==False:
                print('\nTweet classified as a trading tweet:\n', test.iloc[415+i]['text'])
                trade = True
            elif predictions[i] == 1 and tech==False:
                print('\nTweet classified as a technology tweet:\n', test.iloc[415+i]['text'])
                tech = True
            elif predictions[i] == 2 and n==False:
                print('\nTweet classified as a Non subject tweet:\n', test.iloc[415+i]['text'])
                n = True


def main():
    train, target, test = download_data()
    predictions = predict(train, target, test)
    print_pred(predictions)
    print_examples(predictions, test)




if __name__ == "__main__":
    main()
