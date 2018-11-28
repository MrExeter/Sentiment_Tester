from distutils.command.config import config
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json
import sqlite3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from unidecode import unidecode
import time


import os

###############################################################################
#
# Access Twitter API keys from environment file
#
CKEY = os.environ.get('CKEY')
CSECRET = os.environ.get('CSECRET')
ATOKEN = os.environ.get('ATOKEN')
ASECRET = os.environ.get('ASECRET')
#
###############################################################################

analyzer = SentimentIntensityAnalyzer()

the_connection = sqlite3.connect('twitter.db')
the_cursor = the_connection.cursor()


def create_table():
    ###########################################################################
    #
    # Index multiple columns for performance gain, will take more memory though.
    #
    try:
        the_cursor.execute("CREATE TABLE IF NOT EXISTS sentiment(unix REAL, tweet TEXT, sentiment REAL)")
        the_cursor.execute("CREATE INDEX fast_unix ON sentiment(unix)")
        the_cursor.execute("CREATE INDEX fast_tweet ON sentiment(tweet)")
        the_cursor.execute("CREATE INDEX fast_sentiment ON sentiment(sentiment)")
        the_connection.commit()
    except Exception as e:
        print(str(e))


create_table()


class TwitListener(StreamListener):

    def on_data(self, raw_data):
        try:
            ###################################################################
            #
            # Take raw json data and parse.
            # Extract the text and timecode of the tweet
            # Measure the sentiment
            #
            data = json.loads(raw_data)
            tweet = unidecode(data['text'])
            time_ms = data['timestamp_ms']
            vs = analyzer.polarity_scores(tweet)
            sentiment = vs['compound']
            print(time_ms, tweet, sentiment)
            the_cursor.execute("INSERT INTO sentiment (unix, tweet, sentiment) VALUES (?, ?, ?)",
                               (time_ms, tweet, sentiment))
            the_connection.commit()

        except KeyError as e:
            print(str(e))
        return True

    def on_error(self, status_code):
        print(status_code)


while True:
    ############################################################################
    #
    # Access Twitter stream, track all words with vowels, basically get all tweets
    # then selectively analyze for a particular keyword
    #
    # Stay in loop and in case this gets timed out by Twitter, wait 5 seconds and
    # attempt to reconnect
    #

    try:
        auth = OAuthHandler(CKEY, CSECRET)
        auth.set_access_token(ATOKEN, ASECRET)
        twitterStream = Stream(auth, TwitListener())
        twitterStream.filter(track=["a", "e", "i", "o", "u"])
    except Exception as e:
        print(str(e))
        time.sleep(5)


