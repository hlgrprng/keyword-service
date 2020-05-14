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
import requests
import json
import csv
import spacy

nlp = spacy.load('de_core_news_sm')

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
CORS(app)

# seed random number generator
seed(1)

#app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    return "Hello, World!"

nouns = {}
keywords = ['Straße', 'Auto', 'Verkehr', 'Fahrrad', 'Schule']
results = [{
            "id": "82734",
            "scores": {
                "content": 48,
                "response": 23,
                "mutuality": 43,
                "relevance": 22,
                "sentiment": 80
            }
          },
          {
            "id": "82745",
            "scores": {
                "content": 48,
                "response": 23,
                "mutuality": 43,
                "relevance": 22,
                "sentiment": 80
            }
          }
    	]

@app.route('/nlp-services', methods=['POST'])
def get_nlp():
    if not request.json or not 'documents' in request.json or not 'configuration' in request.json:
        abort(400)
    documents = request.json['documents']
    results = []
    for document in documents:
        content = randint(0, 100)
        response = randint(0, 100)
        mutuality = randint(0, 100)
        relevance = randint(0, 100)
        sentiment = randint(0, 100)
        id = document.get('id')
        scores = {
            "content": content,
            "response": response,
            "mutuality": mutuality,
            "relevance": relevance,
            "sentiment": sentiment
        }
        result = {"id" : id , "scores" : scores}
        results.append(result)
    return jsonify({'results': results})
    return request.json

@app.route('/keywordList', methods=['GET'])
def get_keywords():
    return jsonify({'keywords': keywords})

@app.route('/scores', methods=['POST'])
def get_scores():
    get_nlp()
    return jsonify({'results': results})

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

def getKeywordsDBPedia(description):
    tokens = tokenizeDescription(description)
    keywords = set()
    for token in tokens:
        url = app.config['DBPEDIA'] + '?text=' + token + '&confidence=0.2&support=20'
        headers = {'Accept': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Postman-Token': '2349be62-ac5f-4e61-8b27-b01009f3e1d5'}
        response = requests.get(url, headers=headers)
        if 'Resources' in response.json():
            keywords.add(token)
    return list(keywords)

def getKeywordsLeipzig(description):
    tokens = tokenizeDescription(description)
    keywords = set()
    for token in tokens:
        url = app.config['LEIPZIG'] + token
        response = requests.get(url).json()
        if len(response)>0:
            keywords.add(token)
    return list(keywords)

def getKeywordsInternal(description):
    tokens = tokenizeDescription(description)
    keywords = []
    with open(app.config['KEYWORDS'], 'r') as f:
        reader = csv.reader(f)
        keywords = dict(reader)
    results = keywords.keys()
    results = list(set(results).intersection(tokens))
    values = [int(keywords[k]) for k in results]
    results = [x for _,x in sorted(zip(values,results), reverse=True)]
    return results

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
    app.run(debug=True, host='0.0.0.0', port=10001)
