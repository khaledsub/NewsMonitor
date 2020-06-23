from flask import Flask, render_template, request, redirect, session, json, Response, send_file
import pandas as pd
import datetime
from sumrized import Sumrized 
import gensim
from helper import Helper
import nltk, os
import sys
from langdetect import detect
import jwt
import time

app = Flask(__name__)
app.secret_key = 'hackersafar'

myBigdf = pd.DataFrame(columns=['Title', 'Content', 'Tone', 'Goldenstein_Scale', 'Publisher', 'Country',
                                'URL', 'SQLDATE', 'Content_Parsed_6', 'Category', 'Content_Summary'])

def getArticles():
    df = pd.read_csv('GDELT Final.csv', encoding='utf8')
    global w2
    w2 = gensim.models.KeyedVectors.load_word2vec_format('model.bin', 
                                                        binary=True, 
                                                        unicode_errors='ignore',
                                                        limit=50000)
    return df

def returnListFromPandas():
    myoptions = myBigdf[myBigdf.filter(regex='^(?!Unnamed)').columns]
    myoptions['Tone'] = myoptions['Tone'].apply(lambda x: round(x,2))
    myoptions = myoptions.to_json(orient='records')
    return myoptions


@app.route('/articles')
def articles():
    return render_template('layouts/articles.html')

@app.route('/')
def index():
    # METABASE_SITE_URL = "https://nrsc.elm.sa/visualization"
    # METABASE_SECRET_KEY = "12c92d33eef4549621eca2894791e58ae83134892b7b04f8d9f85767407fe282"

    # payload = {
    # "resource": {"dashboard": 1},
    # "params": {
        
    # },
    # "exp": round(time.time()) + (60 * 10) # 10 minute expiration
    # }
    # token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

    # iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token.decode("utf8") + "#bordered=false&titled=false"

    METABASE_SITE_URL = "https://nrsc.elm.sa/visualization"
    METABASE_SECRET_KEY = "12c92d33eef4549621eca2894791e58ae83134892b7b04f8d9f85767407fe282"

    payload = {
    "resource": {"question": 8},
    "params": {
        
    },
    "exp": round(time.time()) + (60 * 10) # 10 minute expiration
    }
    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

    iframeUrl = METABASE_SITE_URL + "/embed/question/" + token.decode("utf8") + "#bordered=true&titled=true"

    return render_template('layouts/index2.html', iframeUrl=iframeUrl)

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    index = request.values.get('index')
    percent = int(request.values.get('percent'))
    body = myBigdf.iloc[int(index)]['Content']
    summary = ''
    print(index, file=sys.stderr)
    try:
        help = Helper(lang='en')
        sentences = help.getArticleSentences(body)
        summarySize = percent # [10, 100]
        limit = ( summarySize * len(sentences) ) / 100

        sumrized = Sumrized('en', w2)
        summary = sumrized.summarize(body, limit)

        if len(summary) <= 20:
            summary = myBigdf.iloc[int(index)]['Content_Summary']
            
    except:
        summary = myBigdf.iloc[int(index)]['Content_Summary']

    return summary

@app.route('/proccess_all')
def proccess_all():
    global myBigdf
    mynewdf = getArticles()
    myBigdf =  mynewdf.copy()

    return returnListFromPandas()

@app.route('/download', methods=['GET', 'POST'])
def download():
    # indices = request.values.get('indices').split(',')
    indices = request.form["indices"].split(',')

    print(indices, file=sys.stderr)
    if indices == ['']:
        myBigdf[myBigdf.filter(regex='^(?!Unnamed)').columns].to_excel('data/report.xlsx', encoding='utf8', index=False)
    else:
        myBigdf[myBigdf.filter(regex='^(?!Unnamed)').columns].iloc[indices].to_excel('data/report.xlsx', encoding='utf8', index=False)
        
    return send_file('data/report.xlsx',
                     attachment_filename='report.xlsx',
                     as_attachment=True)
    # return 'ok'

def toning(x):
    if x > 8: 
        return 'Positive' 
    elif x < -8: 
        return'Negative' 
    else: 
        return'Neutral'

if __name__ == '__main__':
    app.run(debug = True, port=5001,threaded=False)
