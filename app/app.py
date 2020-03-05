from flask import Flask, render_template, request, abort, jsonify, Response, url_for
from requests import get
from bson.objectid import ObjectId
from .config import Config
import boto3, re, time, os, pymongo
import os, re
from flask import send_from_directory
from dlx import DB
from dlx.marc import AuthSet, BibSet, QueryDocument, Condition
import datetime
import json


# Initialize your application.
app = Flask(__name__)
if __name__ == "__main__":
    app.run(host='10.240.200.141', port=8000)

DB.connect(Config.connect_string)
collection = Config.DB.bibs

# Define any classes you want to use here, or you could put
# them in other files and import.
return_data=""
# And start building your routes.

@app.route('/')
def index():
    return(render_template('index.html', data=return_data))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/date')
def date():
    data={}
    current_time = datetime.datetime.now() 
    data['year']=current_time.year
    data['month']=current_time.month
    data['day']=current_time.day
    return(render_template('date.html', data=data))

@app.route('/<date>/xml')
def xml(date):
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    #q=current_time.year+current_time.month+current_time.day
    #else:
        
    query = QueryDocument(
        Condition(
            tag='999',
            #subfields={'z': re.compile('^'+q)}
            subfields={'b': re.compile('^'+str_date)}
            #subfields={'z': str_date}
        ),
        Condition(
            tag='029',
            #subfields={'z': re.compile('^'+q)}
            subfields={'a':'JN'}
        )
    )
    print(query.to_json())
    #bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1}, skip=0, limit=30)
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1}, skip=skp, limit=limt)
    #return_data=bibset.to_xml()
    #print(f"the number of records is {str(bibset.count)}")
    xml=bibset.to_xml()
    return Response(xml, mimetype='text/xml')

@app.route('/<date>/json')
def jsonf(date):
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    #q=current_time.year+current_time.month+current_time.day
    #else:
        
    query = QueryDocument(
        Condition(
            tag='999',
            #subfields={'z': re.compile('^'+q)}
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            #subfields={'z': re.compile('^'+q)}
            subfields={'a':'JN'}
        )
    )
    #bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1}, skip=0, limit=30)
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1})
    #return_data=bibset.to_xml()
    #print(f"the number of records is {str(bibset.count)}")
    jsonl=[]
    for bib in bibset.records:
        jsonl.append(bib.to_json())
    #json=bibset.to_json()
    #return Response(json, mimetype='text/json')
    return jsonify(jsonl)
@app.route('/<date>/symbols')
def symbols(date):
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    #q=current_time.year+current_time.month+current_time.day
    #else:
        
    query = QueryDocument(
        Condition(
            tag='999',
            #subfields={'z': re.compile('^'+q)}
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            #subfields={'z': re.compile('^'+q
            subfields={'a':'JN'}
        )
    )
    #bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1}, skip=0, limit=30)
    bibset = BibSet.from_query(query, projection={'029':1,'191': 1})
    str_out=''
    for bib in bibset.records:
        str_out+=bib.to_str()
    #return_data=bibset.to_xml()
    #print(f"the number of records is {str(bibset.count)}")
    #str=bibset.to_str()
    return Response(str_out, mimetype='text/plain')




    
@app.route('/unbis')
def unbis():
    #str_date=date.replace('-','')
    #print(f"the original str_date is {str_date}")
    #if len(str_date)!= 8:
    #    date = datetime.datetime.now()
    #    str_date=str(date.year)+str(date.month)+str(date.day)
    #print(f"the str_date is {str_date}")
    #q=current_time.year+current_time.month+current_time.day
    #else:
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    print(f"skip is {skp} and limit is {limt}")    
    query = QueryDocument(
        Condition(
            tag='035',
            #subfields={'z': re.compile('^'+q)}
            subfields={'a': re.compile('^T')}
            #subfields={'z': str_date}
        )
    )
    print(query.to_json())
    #bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1}, skip=0, limit=30)
    #authset = AuthSet.from_query(query, projection={'035':1,'150':1,'995':1,'996':1,'997':1, '993':1,'994':1}, skip=skp, limit=limt)
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    #return_data=bibset.to_xml()
    #print(f"the number of records is {str(bibset.count)}")
    unbis=authset.to_xml()
    return Response(unbis, mimetype='text/xml')