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
    #app.run(host='10.240.200.141', port=8000)
    pass

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
    
        
    query = QueryDocument(
        Condition(
            tag='999',
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    print(query.to_json())
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1}, skip=skp, limit=limt)
    xml=bibset.to_xml()
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    return Response(xml, mimetype='text/xml')

@app.route('/<date>/json')
def jsonf(date):
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    
        
    query = QueryDocument(
        Condition(
            tag='999',
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1})
    jsonl=[]
    for bib in bibset.records:
        jsonl.append(bib.to_json())
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
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    bibset = BibSet.from_query(query, projection={'029':1,'191': 1})
    str_out=''
    for bib in bibset.records:
        str_out+=bib.to_str()
    return Response(str_out, mimetype='text/plain')




    
@app.route('/unbis')
def unbis():
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
            subfields={'a': re.compile('^T')}
        )
    )
    print(query.to_json())
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    unbis=authset.to_xml()
    return Response(unbis, mimetype='text/xml')

@app.route('/tcode/<tcode>')
def unbis_tcode(tcode):
    '''
    looks up UNBIS thesaurus T codes and returns matching subject heading records 
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    it uses DLX bibset.to_xml serialization function to output fields 035 and 150 in MARCXML
    '''
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
            subfields={'a': re.compile(str(tcode).upper())}
            )
    )
    print(query.to_json())
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    for auth in authset:
        dict1[auth.get_value('035','a')]=auth.get_value('150','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)


@app.route('/label/<label>')
def unbis_label(label):
    '''
    looks up UNBIS thesaurus labels and returns matching T codes 
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    it uses DLX authset to output fields 035 and 150
    '''
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
            tag='150',
            subfields={'a': re.compile(str(label).upper())}
            )
    )
    print(query.to_json())
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    for auth in authset:
        dict1[auth.get_value('150','a')]=auth.get_value('035','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)

@app.route('/<date>/S')
def jsons(date):
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
        
    query = QueryDocument(
        Condition(
            tag='999',
            subfields={'b': re.compile('^'+str_date)}
        ),
        Condition(
            tag='191',
            subfields={'b': re.compile('^S\/')}
        ) 
    )
    export_fields={'089':1,'191': 1,'239':1,'245':1,'249':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'650':1,'651':1,'710':1,'991':1,'993':1}
    bibset = BibSet.from_query(query, projection=export_fields)
    out_list=[('089','b'),('191','a'),('191','c'),('239','a'),('245','a'),('249','a'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('650','a'),('651','a'),('710','a'),('991','d'),('993','a')]

    jsonl=[]
    
    for bib in bibset.records:
        out_dict={}
        for entry in out_list:
            out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
        jsonl.append(out_dict)
    return jsonify(jsonl)