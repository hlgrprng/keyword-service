#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask
from flask import jsonify
from flask import request
from flask import abort
from flask import send_file
from flask_cors import CORS
from nltk.tokenize import RegexpTokenizer
from random import seed
from random import randint
from random import sample
import requests
import json
import csv
import spacy

from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib
matplotlib.use('agg')
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
document = "Eine Erhol-Oase mit einem zentralen Brunnen und einer steinernen Bank drumrum, auf welcher man verweilen kann. Außerdem gibt es ein bachartiges Gewässer außenrum und Steinplatten, über die man die Wasserflächen queren kann. In den Wasserbecken soll es Fische und Wasserpflanzen geben."
keywords = ['Straße', 'Auto', 'Verkehr', 'Fahrrad', 'Schule']
#wordcloud = "http://mfltricks.files.wordpress.com/2012/04/tagxedo_1.png"
wordcloud = "http://194.95.76.31:10004/get_image"

@app.route('/wordcloud', methods=['POST'])
def get_wordcloud():

    num = 20

    if not request.json or not 'configuration' in request.json :
        abort(400)
    configuration = request.json['configuration']
    num = int(configuration.get('num'))
    print("System - Number of words in Wordcloud " + str(num))

    if not request.json or not 'documents' in request.json :
        abort(400)

    documents = request.json['documents']
    posts = []
    text = ""
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

    return jsonify({'url': getWordcloud(posts, num)})

@app.route('/get_image')
def get_image():
    filename = 'cloud_001.png'
    return send_file(filename, mimetype='image/png')

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


def getWordcloud(posts, num):
    postbody = ""
    for post in posts:
        #print(post.id)
        #print(post.post)
        for word in post.post:
            #print(word)
            postbody = postbody + word + " "

    print("System - String collection for wordcloud complete")
    print(postbody)
    wordcloud_png = WordCloud(background_color="white", max_words=num, max_font_size=100, random_state=45, width=600, height=600, margin=8,).generate(postbody)
    # Display the generated image:
    try:
        plt.rcParams['figure.figsize']=(25,20)
        plt.imshow(wordcloud_png, interpolation='bilinear')
        plt.axis("off")
        plt.savefig('cloud_001.png')
        #plt.show()
    except Exception as e:
        printc("<ERROR> Error, exception<reset>: {}".format(e))
        # 1. The pil way (if you don't have matplotlib)
        printc("<WARNING> Something went wrong with matplotlib, switching to PIL backend... (just showing the image, <red>not<reset> saving it!)")
        #print(postlist)
        #print(len(postlist))

    print("System - Wordcloud available under http://194.95.76.31:10004/get_image")
    return wordcloud

def getKeywordsSpacy(description):
    tokens = tokenizeDescription(description)
    doc = nlp(description)
    keywords = []
    nouns = {}
    for token in doc:
        if (token.pos_ == "NOUN"):
            #print(token.text + " " + token.pos_)
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
    #print(results)
    return results

def tokenizeDescription(description):
    with open(app.config['STOPWORDS'], 'r') as f:
        stopWords = json.load(f)
    tokenizer = RegexpTokenizer(u'[^äüöÄÜÖßa-zA-Z0-9\-]+', gaps=True)
    tokens = tokenizer.tokenize(description)
    tokens = [token for token in tokens if token not in stopWords and token.lower() not in stopWords]
    return tokens

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10004)
