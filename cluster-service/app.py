#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask
from flask import jsonify
from flask import request
from flask import abort
from flask_cors import CORS
from nltk.tokenize import RegexpTokenizer
from random import seed
from random import randint
from random import sample
import requests
import json
import csv
import spacy

from sklearn.decomposition import NMF, LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import concurrent.futures
import time
import pyLDAvis.sklearn
from pylab import bone, pcolor, colorbar, plot, show, rcParams, savefig
import warnings
warnings.filterwarnings('ignore')

from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt

nlp = spacy.load('de_core_news_sm')

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
CORS(app)

# seed random number generator
seed(1)

class Post:
    id = '123'
    title = ""
    post = ""
    sentences = []
    summary = ""
    text = ""
    category = {}
    cluster = ""
    keywords = []
    nouns = {}
    persons = {}
    locations = {}
    geo = []
    sentiment = 0
    sentiPositive = 0
    sentiNegative = 0
    sentiments = []

    relevance = 0
    content = 0
    response = 0
    mutuality = 0

    likes = 0
    comments = 0

    def __init__(self, id, title, post):
        self.id = id
        self.title = title
        self.post = post

    def addCategory(self, category):
        self.category = category


#app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    return "Hello, World!"

nouns = {}
keywords = ['Straße', 'Auto', 'Verkehr', 'Fahrrad', 'Schule']

@app.route('/clustering', methods=['POST'])
def get_cluster():
    clusterCount = 3

    print(request.json)
    if not request.json or not 'configuration' in request.json :
        abort(400)
    configuration = request.json['configuration']
    clusterCount = int(configuration.get('clusterCount'))
    print("System - Number of clusters " + str(clusterCount))

    if not request.json or not 'documents' in request.json :
        abort(400)

    documents = request.json['documents']
    posts = []
    for document in documents:
        post = Post
        if document.get('id'):
            id = document.get('id')
            #print(id)
            title = document.get('title')
            if document.get('tags'):
                tags = document.get('tags')
                #print(tags)
            elif document.get('body') :
                description = document.get('body')
                #print(description)
                tags = getKeywordsSpacy(description)
                #print(list(tags))
                post = Post(id, title, tags)
                #print(post)
                posts.append(post)
            else:
                abort(400)
        else:
            abort(400)

    return jsonify({'results': getCluster(posts, clusterCount)})

@app.route('/keywords', methods=['POST'])
def suggest_keywords():
    if not request.json or not 'description' in request.json or not 'mode' in request.json:
        abort(400)
    description = request.json['description']
    mode = request.json['mode']
    externalService = request.json['externalService']
    url = request.json['url']
    num = int(request.json['num'])
    if mode=='internal':
        return jsonify(getKeywordsSpacy(description)[:num]), 201
    elif mode=='external':
        if externalService=='DBPedia':
            return jsonify(getKeywordsSpacy(description)[:num]), 201
#    		return jsonify(getKeywordsDBPedia(description)[:num]), 201
        else:
            return jsonify(getKeywordsSpacy(description)[:num]), 201
#    		return jsonify(getKeywordsLeipzig(description)[:num]), 201
    else:
        abort(400)

def getCluster(posts, clusterCount):

    postlist = []
    for post in posts:
        print(post.id)
        print(post.post)
        cluster_keys = ' '.join(list(post.post))
        postlist.append(cluster_keys)
    print(postlist)
    print(len(postlist))

    try:
        vectorizer = CountVectorizer(min_df=0.2, max_df=2.9, lowercase=False)
        #vectorizer = TfidfVectorizer()
        data_vectorized = vectorizer.fit_transform(postlist)
        # 3 subtopics
        NUM_TOPICS = clusterCount
        lda = LatentDirichletAllocation(n_components=NUM_TOPICS, max_iter=15, learning_method='online',verbose=True)
        data_lda = lda.fit_transform(data_vectorized)

        nmf = NMF(n_components=NUM_TOPICS)
        data_nmf = nmf.fit_transform(data_vectorized)
        lsi = TruncatedSVD(n_components=NUM_TOPICS)
        data_lsi = lsi.fit_transform(data_vectorized)

        print("Topics")

        topicmap = []
        for index, topic in enumerate(lda.components_):
            topics = [(vectorizer.get_feature_names()[i]) for i in topic.argsort()[-3:]]
            topicmap.append(topics)
            print(f'Top 5 words for Topic #{index}')
            print([vectorizer.get_feature_names()[i] for i in topic.argsort()[-5:]])
            print('\n')

        clusters = []
        for topic in topicmap:
            title = ""
            print(topic)
            for top in topic:
                title = title + top + " "
            cluster = {"title" : title, "ids" : getTopicIds(posts, topic)}
            clusters.append(cluster)

    except Exception as e:
        print("<ERROR> Error, exception<reset>: {}".format(e))
        # 1. The pil way (if you don't have matplotlib)
        print("<WARNING> Something went wrong with clustering")
        clusters = []

        #print(postlist)
        #print(len(postlist))    #vectorizer = CountVectorizer(min_df=5, max_df=0.9, stop_words='german', lowercase=True, token_pattern='[a-zA-Z\-][a-zA-Z\-]{2,}')


    return clusters

def getTopicIds(posts, topics):
    topicPosts = []
    #print(topics)
    for topic in topics:
        for post in posts:
            #print(post.id)
            for word in post.post:
                #print(topic)
                if word == topic:
                    #print(post.id)
                    if post.id not in topicPosts:
                        topicPosts.append(post.id)
    return topicPosts


def getKeywordsSpacy(description):
    tokens = tokenizeDescription(description)
    doc = nlp(description)
    keywords = []
    nouns = {}
    for token in doc:
        if (token.pos_ == "NOUN"):
            print(token.text + " " + token.pos_)
            if token.text not in keywords:
                keywords.append(token.text)
            if token.text in nouns:
                nouns[token.text] = nouns[token.text] + 1
            else:
                nouns[token.text] = 1
    results = nouns.keys()
    values = [int(nouns[k]) for k in results]
    results = [x for _,x in sorted(zip(values,results), reverse=True)]
    #results = {k: v for k, v in sorted(nouns.items(), key=lambda item: item[1])}
    print(results)
    return results

def tokenizeDescription(description):
    with open(app.config['STOPWORDS'], 'r') as f:
        stopWords = json.load(f)
    tokenizer = RegexpTokenizer(u'[^äüöÄÜÖßa-zA-Z0-9\-]+', gaps=True)
    tokens = tokenizer.tokenize(description)
    tokens = [token for token in tokens if token not in stopWords and token.lower() not in stopWords]
    return tokens

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10002)
