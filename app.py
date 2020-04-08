#!/usr/bin/env python3
# -*- coding: utf-8 -*-	
from flask import Flask
from flask import jsonify
from flask import request
from flask import abort
from flask_cors import CORS
from nltk.tokenize import RegexpTokenizer
import requests
import json
import csv

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
CORS(app)

#app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    return "Hello, World!"

keywords = ['Straße', 'Auto', 'Verkehr', 'Fahrrad', 'Schule']

@app.route('/keywordList', methods=['GET'])
def get_keywords():
    return jsonify({'keywords': keywords})

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
    		return jsonify(getKeywordsInternal(description)[:num]), 201
    elif mode=='external':
    	if externalService=='DBPedia':
    		return jsonify(getKeywordsInternal(description)[:num]), 201
#    		return jsonify(getKeywordsDBPedia(description)[:num]), 201
    	else:
    		return jsonify(getKeywordsInternal(description)[:num]), 201
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

def tokenizeDescription(description):
	with open(app.config['STOPWORDS'], 'r') as f:
		stopWords = json.load(f)
	tokenizer = RegexpTokenizer(u'[^äüöÄÜÖßa-zA-Z0-9\-]+', gaps=True)
	tokens = tokenizer.tokenize(description)
	tokens = [token for token in tokens if token not in stopWords and token.lower() not in stopWords]
	return tokens

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10001)
