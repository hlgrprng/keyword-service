# keyword-service

## Introduction

The keyword service is a micro-service that suggests keywords to ideas using external services like Wortschatz Leipzig and DBPedia.

## Installation

```sh
$ pip install -r requirements.txt
$ python app.py
```
The following message should be then displayed:

```sh
Debug mode: on
Running on http://0.0.0.0:10001/ (Press CTRL+C to quit)
Restarting with stat
Debugger is active!
Debugger PIN: 161-064-190
```


## Usage

POST request to `/keywords`

Body:

```
{
    "description": "Eine Erhol-Oase mit einem zentralen Brunnen und einer steinernen Bank drumrum, auf welcher man verweilen kann. Außerdem gibt es ein bachartiges Gewässer außenrum und Steinplatten, über die man die Wasserflächen queren kann. In den Wasserbecken soll es Fische und Wasserpflanzen geben.",
    "mode": "external",
    "externalService": "DBPedia",
    "url": "http://keywordset.net",
    "num": 6
}
```

Result:

```
[
    "geben",
    "Gewässer",
    "Brunnen",
    "Bank",
    "Wasserpflanzen",
    "zentralen"
]
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
