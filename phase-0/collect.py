"""
Collect data.
this code serves 2 purposes under the broader category of data collection

    1. A pickle file called user.pkl, which is essentially an adjacency matrix
       but I am choosing to store it as a DataFrame for ease right now
    2. A pickle file called tweets.pkl which is a collection of 5 tweets from 
       each user i have sampled from the user dataframe.  These will be used for 
       classification

"""
import time
import sys
import configparser
from TwitterAPI import TwitterAPI
import pandas as pd
from collections import Counter
import networkx as nx
import matplotlib.pyplot as plt
def get_twitter(config_file):
    """ Read the config_file and construct an instance of TwitterAPI.
    Args:
      config_file ... A config file in ConfigParser format with Twitter credentials
    Returns:
      An instance of TwitterAPI.
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    twitter = TwitterAPI(
                   config.get('twitter', 'consumer_key'),
                   config.get('twitter', 'consumer_secret'),
                   config.get('twitter', 'access_token'),
                   config.get('twitter', 'access_token_secret'))
    return twitter

def read_screen_names(filename):
    '''
    read a text file containing twitter screen_names 
    return a list of strings 
    '''
    screen_names = open(filename).read().split('\n')
    screen_names = list(filter(None, screen_names))
    return screen_names



def robust_request(twitter, resource, params, max_tries=10, flag = False):
    '''
    if a request fails, retry in 15 minutes
    I may adjust this soon
    '''
    for i in range(max_tries):
        request = twitter.request(resource, params)
        if request.status_code == 200:
            return request
        elif request.status_code == 401 and flag == True:
            return 
        else:
            print('Got error {0} \nsleeping for 15 minutes... sucks'.format(request.text))
            print(time.asctime( time.localtime(time.time()) ))
            sys.stderr.flush()
            time.sleep(60*15 + 1)

def get_users(twitter, screen_names):
    '''
    Retrieve twitter user objects for each screen name
    params:
        tiwtter : a twitterapi object
        screen_names : a list of strings, for each twitter use you wnat to search
    returns:
        a list of dicts, one per user

    docs: https://dev.twitter.com/rest/reference/get/users/lookup
    '''

    users = robust_request(twitter, 'users/lookup',{'screen_name':screen_names})
    return users 




def get_friends(twitter, screen_name, limit = 5000):
    '''
    returns a list of twitter IDs for users which this user follows, up to 5k
    docs: https://dev.twitter.com/rest/reference/get/friends/ids
    params:
        twitter : a twitterapi object
        screen_names : strong of twitter screen name
    returns:
        A list of ints, sorted in accending order. one per friend ID
    
    limit will initially be set to 5k, but can be adjusted based on application
    '''
    f = robust_request(twitter, 'friends/ids',
            {'screen_name':screen_name, 'count':limit})
    return sorted(f.json()['ids'])


def add_all_friends(twitter, users):
    '''
    get a list of accounts each user follows.
    help
    '''
    for u in users: 
        friends = get_friends(twitter, u['screen_name'])
        u['friends'] = friends

def print_num_friends(users):
    '''
    print number of friends per user, sorted by user name
    '''
    users.sort(key=lambda k: k['name'])
    for u in users:
        print(u['screen_name'], len(u['friends']))

def count_friends(users):
    '''
    count how often each friend is followed
    users:list of user dicts
    
    returns:
        a Counter object mapping each friend to the number of candidates who follow them.
    '''
    c = Counter()
    for u in users:
        c.update(u['friends'])
    return c


def friend_overlap(users):
    '''
    Compute the number of shared accounts followed by each pair of users.
    '''
    overlap = []
    for u in range(len(users)):
        for v in range(u,len(users)):
            if u != v:
                overlap.append((users[u]['screen_name'],users[v]['screen_name'],
                    len(list((Counter(users[u]['friends']) & Counter(users[v]['friends'])).elements()))))

    
    
                return sorted(overlap, key=lambda x:x[-1],reverse=True)



def create_df(users):
    '''
    create a dataframe between friends and users I am searching
    basically i am creating an adjacency matrix, but i will 
    put it in a dataframe for future use 
    '''
    f = sorted(set([i for j in [user['friends'] for user in users] for i in j]))
    all_friends = f.copy()
    f = {'ids':f}
    for u in users:
        f[u['id']] = []
        for friend in f['ids']:
            if friend in set(u['friends']):
                f[u['id']].append(1)
            else:
                f[u['id']].append(0)

    data = pd.DataFrame(data = f)

    data.to_pickle("./user.pkl")
    return all_friends

def search_tweets(twitter, query, count = 30, result_type = 'recent'):
    '''
    returns a list of tweets based on the specifications entered
    this is very primitive because I do not have access to sophisticated 
    search parameters
    params:
        twitter : a twitterapi object
        query : a string to query 
        count : the number of tweets to return, max = 100
    returns:
        a list of tweet objects
    '''
    tweets = robust_request(twitter, 'search/tweets',
            {'q':query, 'count':count, 'result_type':result_type})
    return tweets


def gather_tweets(twitter, users, count = 5):
    '''
    first attempt to gather many tweets 
    will update as i proceed
    '''
    master_tweets = []
    print('collecting tweets from {0} users'.format(len(users)))
    for user in users:
        try:
            request =  robust_request(twitter, 'statuses/user_timeline', {'user_id': user, 'count': count},flag = True)
            if request:
                tweets = [i for i in request]
                master_tweets.extend(tweets)
        except:
            print("Waiting 10 seconds...")
            time.sleep(10)
    print('Gathered a total of {0} tweets'.format(len(master_tweets)))
    tweet_df = pd.DataFrame(master_tweets)
    tweet_df.to_pickle('./tweets.pkl')


def create_graph(users,all_friends,  friend_counts):
    graph = nx.Graph()
    #for u in users:
       # graph.add_node(u['id'])
    graph.add_nodes_from(all_friends)
    for u in users:
        for f in u['friends']:
            graph.add_edge(u['id'],f)

    for i in graph.copy().node:
        if graph.degree(i) < 2:
            graph.remove_node(i)

    return graph
    

def gather_t2(twitter, users):
    '''
    gather the timeline of the screen_names i am inspecting: the 8 "leaders"

    '''
    master_tweets = []
    for user in users:
        count = 0
        request =  robust_request(twitter, 'statuses/user_timeline', {'screen_name': user, 'trim_user':True, 'count':200 })
        try:
            while count < 5:
                tweets = [i for i in request]
                master_tweets.extend(tweets)
                request = robust_request(twitter, 'statuses/user_timeline', {'screen_name': user, 'trim_user':True, 'count':200,'max_id':tweets[-1]['id']})
                count += 1 
            print('User: {0}, Total tweets collected: {1}'.format(user,len(master_tweets)))
        except: # incase someones timeline is not long enough 
            continue
    tweets_df = pd.DataFrame(master_tweets)
    tweets_df.to_pickle('./main_user_tweets.pkl')




def main():
    twitter = get_twitter('../twitter.cfg')
    screen_names = read_screen_names('./users.txt')
    print('Connected to twitter successfully')
    #print('Using the following screen names:\n {0}'.format(screen_names))
    users = sorted(get_users(twitter, screen_names), key=lambda x: x['screen_name'])
    print('found {0} users with screen_names {1}'.format(len(users), str([u['screen_name'] for u in users]))) 
    add_all_friends(twitter, users)
    #print('Friends per User:')
    #print_num_friends(users)
    all_friends = create_df(users)
    friend_counts = count_friends(users)
       

    gather_tweets(twitter, all_friends)
    gather_t2(twitter, screen_names)

    graph = create_graph(users, all_friends, friend_counts)
    nx.write_gpickle(graph, './graph.gpickle')


if __name__ == "__main__":
    main()
