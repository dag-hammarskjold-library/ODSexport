from posixpath import split
from flask import Flask, render_template, request, abort, jsonify, Response, url_for, send_file, redirect
from flask import Flask, render_template, request
from requests import get
from bson.objectid import ObjectId
from bson import SON
from bson.json_util import dumps, loads
from .config import Config
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collation import Collation
import boto3, re, time, os, pymongo
import os, re
from flask import send_from_directory
from dlx import DB
from dlx.marc import AuthSet, BibSet, Query, QueryDocument, Condition
from dlx.file import File, Identifier
from .decorate import add_856, elem_856
#import datetime
import json
#import datetime
from datetime import datetime, date
from datetime import timedelta
import requests
import json
import ssl
import certifi
from io import BytesIO
from urllib.parse import quote, unquote
ssl._create_default_https_context = ssl._create_unverified_context


'''
simple test URLs
/20200707/xml?skip=10&limit=35
/20200707/json?skip=10&limit=35
/unbis?skip=10&limit=35
/20200707/S?skip=10&limit=35
/2020-07-07/S?skip=10&limit=35


'''
# Initialize your application.
app = Flask(__name__)
if __name__ == "__main__":
    pass
#dbname = client.get_parameter(Name='dbname')['Parameter']['Value']
#DB.connect(dbname)
#collection = Config.DB.bibs
#toconnect to itpp sections
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI, tlsCAFile=certifi.where())
myDatabase=myClient['undlFiles']
DB.connect(myMongoURI, database='undlFiles')
collection = myDatabase.bibs
filesColl=myDatabase.files

#sectionOutput = "itp_sample_output_copy"
#sectionsCollection=myDatabase[sectionOutput]
#sectionsCollection=Config.DB.itp_sample_output_copy
# Define any classes you want to use here, or you could put
# them in other files and import.
client_dev_atlas=MongoClient(Config.connect_string_dev_atlas, tlsCAFile=certifi.where())
db_dev_atlas=client_dev_atlas['itpp']
sectionOutput = "itp_sample_output_copy"
sectionsCollection=db_dev_atlas[sectionOutput]

return_data=""

# Start building your routes.

@app.route('/')
def index():
    return(render_template('index.html', data=return_data))


@app.route('/baskt_users')
def users():
    users = []
    baskets_by_user = {}
    db=myDatabase
    # Retrieve user information and baskets from MongoDB
    for user in db.user.find():
        user_data = {'_id': str(user['_id']), 'name': user['username']}
        users.append(user_data)
        baskets = []
       
        for basket in db.basket.find({'owner': user['_id'], 'items':{"$exists":True}}):
            for item in basket['items']:
                basket_data = {'collection': item['collection'], 'record_id': item['record_id']}
                baskets.append(basket_data)

        baskets_by_user[str(user['_id'])] = baskets
    
    
    
    # Render the template with the user and basket data
    return render_template('baskt_users.html', users=users, baskets_by_user=baskets_by_user)

@app.route('/pdf/<path:path>')
def show_pdf(path):
    xfile = File.latest_by_identifier_language(Identifier('symbol', path), 'EN')
    print(xfile.uri)
    return(render_template('test1.html', symbol=path,uri='http://'+xfile.uri))
    
@app.route('/test1')
def test1():
    return(render_template('toods2.html', data=return_data))

@app.route('/intoods')
def toods():
    return(render_template('toods.html', data=return_data))

@app.route('/exporttoods',methods=['GET','POST'])
def exporttoods():
    #form = "toods"
    symbols=request.form.get("symboltoODS")
    print(f"symbols are {symbols} ")
    response_dict=export_to_ods(symbols)
    return(render_template('toods.html', response_dict=response_dict))

def export_to_ods(symbols):
    token_url="https://api.un.org/token"
    by_symbol_host="https://api.un.org/un/library/ods/v1/record"

    #symbols = path.split()
    ssm_client = boto3.client('ssm')
    odsapitoken = ssm_client.get_parameter(Name='ods-api-token')['Parameter']['Value']
    payload='grant_type=client_credentials'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Basic ' + odsapitoken
    }

    try:    
        response = requests.request("POST", token_url, headers=headers, data=payload)
        response_text=json.loads(response.text)
        #print(response_text)
        access_token=response_text.get('access_token')
        #print(f" access token is {access_token}")
    except:
        raise

    hdrs={"Authorization":"Bearer "+access_token}

    for symbol in symbols.split():
        prmtrs={"symbol":symbol}
        print(f"symbol in the loop is {symbol}")
        try:
            result=requests.get(
                url=by_symbol_host,
                headers=hdrs,
                params=prmtrs
            )
            print(result.text)
        except: 
            print(f"something is wrong")
            raise
    return ("Symbols {} sent to ODS".format(symbols))
    #return(render_template('toods.html', response_dict = result.json))

'''show json itpp itp'''
@app.route('/itp/<path:path>')
def itp(path):
    '''
    outputs records in native central DB schema json format for the section/body/session which is provided as a dynamic route 
    e.g. /subj/A/76
    e.g. /subj/A/76?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    #if the date is in wrong format the function returns today's records
    it uses DLX's bibset.to_json serialization function to output json
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
    inpt_list=path.split("/")
    if inpt_list[0].lower() in ["itsp", "itss", "itsc","subj", "age", "vot", "dsl","meet","reps","sor","res"]:
        pass
    else:
        inpt_list[0]=""
    bodysession=inpt_list[1].upper()+"/"+inpt_list[2]

    itsps=sectionsCollection.find({"$and":[{'section':'itp'+inpt_list[0].lower()},{'bodysession':bodysession}]},{"_id": 0, "sort":0,"section":0},skip=skp, limit=limt)
    #print (itsps)
    #cursl=[dumps(itsp) for itsp in itsps]
    #for itsp in itsps:
    #    jsonl.append(itsp) 
    #    #print(itsp.to_json())
    #return [strng.encode('utf-8') for strng in cursl]
    #return jsonify(itsps)
    return jsonify([itsp for itsp in itsps])


@app.route('/file_upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return render_template('file_upload_and_contents.html', error='No file part')
        
        file = request.files['file']
        
        # If user does not select file, browser also submit an empty part without filename
        if file.filename == '':
            return render_template('file_upload_and_contents.html', error='No selected file')
        
        if file:
            # Save the uploaded file to the uploads folder
            file_path = os.path.join('', file.filename)
            file.save(file_path)
            
            # Open the uploaded file and read its contents
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Render the file_contents.html template with the file contents
            return render_template('file_uc1.html', content=content)
    
    # If the request method is GET or the form has not been submitted yet, render the file_upload.html template
    return render_template('file_uc1.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
@app.route('/date')
def date():
    '''
    returns the current date - for test purposes
    '''
    data={}
    current_time = datetime.now() 
    data['year']=current_time.year
    data['month']=current_time.month
    data['day']=current_time.day
    return(render_template('date.html', data=return_data))


@app.route('/<date>/xml856')
def xml856(date):
    '''
outputs records in MARCXML format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
/YYYYMMDD/xml?skip=n&limit=m
skip=n URL parameter is used to skip n records. Default is 0.
limit=m URL parameter is used to limit number of records returned. Default is 50.
if the date is in wrong format the function returns today's records
it uses DLX bibset.to_xml serialization function to output MARCXML
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
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")     
    query = Query(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        ),
        Condition(
            tag='930',
            subfields={'a':'DIG'}
        )
    )
    #print(query.to_json())
    sel_query={"930.subfields.value":"DIG","029.subfields.value":"JN"}
    dict_query=date_query(str_date,**sel_query)
    bibset = BibSet.from_query(dict_query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'856':1,'991':1}, skip=skp, limit=limt)
    ts3=time.time()
    xml=add856(bibset)
    print(f"total time for adding 856 is {time.time()-ts3}")
    #xml=bibset.to_xml()
    #decoding to string and emoving double space from the xml; creates pbs with the job number on ODS export
    xml=xml.decode("utf-8").replace("  "," ")
    return Response(xml, mimetype='text/xml')


@app.route('/<ldate>/xml')
def xml(ldate):
    '''
outputs records in MARCXML format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
/YYYYMMDD/xml?skip=n&limit=m
skip=n URL parameter is used to skip n records. Default is 0.
limit=m URL parameter is used to limit number of records returned. Default is 50.
if the date is in wrong format the function returns today's records
it uses DLX bibset.to_xml serialization function to output MARCXML
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
    str_date=ldate.replace('-','')
    print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        ldate = datetime.now()
        str_date=str(ldate.year)+str(ldate.month)+str(ldate.day)
        date_year,date_month, date_day = ldate.year, ldate.month, ldate.day
        date_from=ldate
    else:   
        date_year=str_date[0:4]
        date_month=str_date[4:6]
        date_day=str_date[6:8]
    date_from=datetime.strptime(date_year+"-"+date_month+"-"+date_day, "%Y-%m-%d")
    #date_from=date.fromisoformat(date_year+"-"+date_month+"-"+date_day)
    #date_to=date_from+timedelta(days = 2)
    print(f"date_from is {date_from}")
    #print(f"date_to is {date_to}")
    dict_query= {"$and":[{"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)}},{"029.subfields.value":"JN"}]}  
    #dict_query= {"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)}}
    #print(query.to_json())
    #print(f"son query is {son_query}")
    print(f"dict query is {dict_query}")
    start_time=datetime.now()
    bibset = BibSet.from_query(dict_query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1}, skip=skp, limit=limt)
    xml=bibset.to_xml()
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    print(f"duration for updated was {datetime.now()-start_time}")
    return Response(xml, mimetype='text/xml')

@app.route('/<date>/json')
def jsonf(date):
    '''
    outputs records in native central DB schema json format for the date which is provided as a dynamic route inputed in YYYYMMDD or YYYY-MM-DD
    e.g. /YYYY-MM-DD/json
    e.g. /YYYYMMDD/json?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it uses DLX's bibset.to_json serialization function to output json
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    #print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    #print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    #print(f"the str_date is {str_date}")
    query = Query(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    sel_query={"029.subfields.value":"JN"}
    dict_query=date_query(str_date, **sel_query)
    bibset = BibSet.from_query(dict_query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1,'998':1}, skip=skp, limit=limt)

    jsonl=[]
    for bib in bibset.records:
        jsonl.append(bib.to_json())
    return jsonify(jsonl)



@app.route('/gatables/<path:path>')
def jsonfga(path):
    '''
    outputs records in native central DB schema json format for the body/session which is provided as a dynamic route inputed as e.g. A/76
    e.g. /gatables/A/76
    e.g. /gatables/A/76?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    #if the date is in wrong format the function returns today's records
    it uses DLX's bibset.to_json serialization function to output json
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
    #str_date=date.replace('-','')
    #print(f"the original str_date is {str_date}")
   # if len(str_date)!= 8:
        #date = datetime.datetime.now()
        #str_date=str(date.year)+str(date.month)+str(date.day)
   # print(f"the str_date is {str_date}")
    inpt_list=path.split("/")
    print(inpt_list)
    #query is 791:"A76" AND 930:VOT
    query = Query(
        Condition(
            tag='791',
            subfields={'b': str(inpt_list[0]+'/')}
        ),
        Condition(
            tag='791',
            subfields={'c':str(inpt_list[1])}
        ),
        Condition(
            tag='930',
            subfields={'a':"VOT"}
        )
    )
    #print (query.to_json())
    bibset = BibSet.from_query(query, projection={'245':1,'269':1,'590':1,'791':1,'952':1,'991':1,'992':1,'993':1,'996':1},sort=[('992.subfields.value',-1),('_id',-1)],skip=skp, limit=limt)
    out_list=[('245','a'),('269','a'),('590','a'),('791','a'),('791','c'),('952','a'),('991','b'),('992','a'),('993','a'),('996','a')]
    
    jsonl=[]
    
    for bib in bibset.records:
        out_dict={}
        
        for entry in out_list:
            out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            
        jsonl.append(out_dict)
    def sort_l(e):
        #print(e['791__a'][0][e['791__a'][0].rindex('/')+1:])
        sorted_s=e['791__a'][0][e['791__a'][0].rindex('/')+1:]
        #sorted_s=e['791__a'][0][e['791__a'][0].rindex('/')+1:].replaceAll("[a-zA-Z[]-]","")
        sorted_ss = re.sub('\D', '', sorted_s)
        return int(sorted_ss)

    jsonl.sort(key=sort_l, reverse=True)

    return jsonify(jsonl)





@app.route('/ds/<path:path>')
def show_txt(path):
    ts2=time.time()
    #query = Query.from_string("symbol:"+'"'+path+'"') # Dataset-search_query
    query = Query.from_string("191__a:'"+path+"'") # Dataset-search_query f"191__a:'{path}'""

    #query = QueryDocument(
     #   Condition(
     #       tag='191',
     #       #subfields={'a': re.compile('^'+path+'$')}
     #       subfields={'a': path}
     #   )
    #)
    #print(f" the imp query is  -- {query.to_json()}")
    #export_fields={'089':1,'091':1,'191': 1,'239':1,'245':1,'249':1,'260':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'630:1,''650':1,'651':1,'710':1,'981':1,'989':1,'991':1,'992':1,'993':1,'996':1}
    bibset = BibSet.from_query(query)
    out_list=[('089','b'),('091','a'),('191','a'),('191','b'),('191','c'),('191','9'),('239','a'),('245','a'),('245','b'),('245','c'),('249','a'),('260','a'),('260','b'),('260','c'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('630','a'),('650','a'),('651','a'),('710','a'),('981','a'),('989','a'),('989','b'),('989','c'),('991','a'),('991','b'),('991','c'),('991','d'),('992','a'),('993','a'),('996','a')]
    #print(f"duration for query was {datetime.now()-start_time_query}")
    #print(f"time for query is {time.time()-ts2}")
    jsonl=[]
    #print(f"time for query is {time.time()-ts2}")
    for bib in bibset.records:
        
        out_dict={}
        #start_time_bib=datetime.now()
        for entry in out_list:
            #start_time_field=datetime.now()
            out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            #print(f"for the field {entry[0]+'__'+entry[1]}")
            #print(f"duration for getting values was {datetime.now()-start_time_field}")
        jsonl.append(out_dict)
        #print(f"for the bib {bib.get_values('191','a')}")
        #print(f"duration for getting bib values was {datetime.now()-start_time_bib}")
    #print(f"total duration was {datetime.now()-start_time_all}")
    return jsonify(jsonl)


@app.route('/xml/<path:path>')
def show_xml(path):
    #query = QueryDocument(
     #   Condition(
      #      tag='191',
       #     #subfields={'a': re.compile('^'+path+'$')}
        #    subfields={'a': path}
        #)
    #)
    query = Query.from_string("symbol:"+path) # Dataset-search_query
    #print(f" the imp query is  -- {query.to_json()}")
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'856':1,'991':1, '998':1})
    xml=bibset.to_xml()
    #removing double space from the xml; creates pbs with the job number on ODS export
    xml=xml.replace("  "," ")
    return Response(xml, mimetype='text/xml')

#add856 # this is to insert 856 tags with PDF files info into xml
@add_856
def add856(bibset):
    return bibset.to_xml()



@app.route('/xml856/<path:path>')
def show_xml856(path):
    #query = QueryDocument(
     #   Condition(
     #       tag='191',
     #       #subfields={'a': re.compile('^'+path+'$')}
     #       subfields={'a': path}
     #   )
    #)
    query = Query.from_string("symbol:"+path) # Dataset-search_query
    #print(f" the imp query is  -- {query.to_json()}")
    ts2=time.time()
    bibset = BibSet.from_query(query, projection={'029':1,'091':1,'191': 1,'245':1,'269':1,'650':1,'991':1})
    #add856 # this is where we insert 856 tags for files info
    #print(f"time for query is {time.time()-ts2}")
    ts3=time.time()
    xml=add856(bibset)
    #print(f"total time for adding 856 is {time.time()-ts3}")
    #xml=bibset.to_xml()
    #decoding to string and emoving double space from the xml; creates pbs with the job number on ODS export
    xml=xml.decode("utf-8").replace("  "," ")
    return Response(xml, mimetype='text/xml')






@app.route('/unbis')
def unbis():

    '''
    outputs UNBIS thesaurus subject heading records in MARCXML format /unbis?skip=n&limit=m
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
    query = Query(
            Condition(
            tag='035',
            subfields={'a': re.compile('^[PT]')}
            )
    )
    #print(query.to_json())
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    unbis=authset.to_xml()
    return Response(unbis, mimetype='text/xml')



@app.route('/<date>/unbis')
def date_unbis(date):
    '''
    outputs records in native central DB schema json format for the date which is provided as a dynamic route inputed in YYYYMMDD or YYYY-MM-DD
    e.g. /YYYY-MM-DD/json
    e.g. /YYYYMMDD/json?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it uses DLX's bibset.to_json serialization function to output json
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    #print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    print(f"the original str_date is {str_date}")
    #if len(str_date)!= 8:
        #date = datetime.datetime.now()
        #str_date=str(date.year)+str(date.month)+str(date.day)
    print(f"the str_date is {str_date}")
    query = Query(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
            ),
        Condition(
            tag='035',
            subfields={'a': re.compile('^T')}
            )
        )
    sel_query={"035.subfields.value":{"$regex":"^T"}}
    dict_query=date_query(str_date,**sel_query)  
    #print(query.to_json()) "191.subfields.value":{"$regex":"^S\/"}
    '''
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    unbis=authset.to_xml()
    return Response(unbis, mimetype='text/xml')
    '''
    dict1={}
    authset = AuthSet.from_query(dict_query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    for auth in authset:
        val_035a=auth.get_values('035','a')
        #print(f"035 values are: {val_035a}")
        val_035a=''.join([str for str in val_035a if str[0]=='T'])
        #dict1[auth.get_value('035','a')]=auth.get_value('150','a')
        dict1[val_035a]=auth.get_value('150','a')
        #dict1['FR']=auth.get_value('993','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)

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
    #print(f"skip is {skp} and limit is {limt}")    
    query = Query(
        Condition(
            tag='035',
            subfields={'a': re.compile(str(tcode).upper())}
            )
    )
    #print(query.to_json())
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1,'993':1,'994':1,'995':1, '996':1, '997':1}, skip=skp, limit=limt)
    for auth in authset:
        val_035a=auth.get_values('035','a')
        #print(f"035 values are: {val_035a}")
        val_035a=''.join([str for str in val_035a if str[0]=='T'])
        #dict1[auth.get_value('035','a')]=auth.get_value('150','a')
        dict1[val_035a]={'EN':auth.get_value('150','a'),'FR':auth.get_value('993','a'),'ES':auth.get_value('994','a'),'AR':auth.get_value('995','a'), 'ZH':auth.get_value('996','a'),'RU':auth.get_value('997','a')}
        #dict1['FR']=auth.get_value('993','a')
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
    #print(f"skip is {skp} and limit is {limt}")    
    query = Query(
        Condition(
            tag='150',
            subfields={'a': re.compile(str(label).upper())}
            )
    )
    #print(query.to_json())
    dict1={}
    authset = AuthSet.from_query(query, projection={'035':1,'150':1}, skip=skp, limit=limt)
    '''
    for auth in authset:
        dict1[auth.get_value('150','a')]=auth.get_value('035','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)
    '''

    for auth in authset:
        val_035a=auth.get_values('035','a')
        #print(f"035 values are: {val_035a}")
        val_035a=''.join([str for str in val_035a if str[0]=='T'])
        #dict1[auth.get_value('035','a')]=auth.get_value('150','a')
        dict1[auth.get_value('150','a')]=val_035a
        #dict1['FR']=auth.get_value('993','a')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    return jsonify(dict1)

def date_query(str_date, **sel_query):  
    if len(str_date)!= 8:
        ldate = datetime.now()
        str_date=str(ldate.year)+str(ldate.month)+str(ldate.day)
        date_year,date_month, date_day = ldate.year, ldate.month, ldate.day
        date_from=ldate
    else:   
        date_year=str_date[0:4]
        date_month=str_date[4:6]
        date_day=str_date[6:8]
    date_from=datetime.strptime(date_year+"-"+date_month+"-"+date_day, "%Y-%m-%d")
    dict_query= {"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)}}
    dict_query.update(sel_query)
    return dict_query



@app.route('/<date>/S')
def jsons(date):
    '''
    outputs Security Council bib records in plain simple json format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
    e.g. /YYYY-MM-DD/xml?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it is used to publish S/ records for iSCAD+ in a plain json
    22 July added fields 049:a and 260:a
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    #print(f"skip is {skp} and limit is {limt}")    
    #start_time_all=datetime.now()
    str_date=date.replace('-','')

    #print(f"the original str_date is {str_date}")
    if len(str_date)!= 8:
        ldate = datetime.now()
        str_date=str(ldate.year)+str(ldate.month)+str(ldate.day)
        date_year,date_month, date_day = ldate.year, ldate.month, ldate.day
        date_from=ldate
    else:   
        date_year=str_date[0:4]
        date_month=str_date[4:6]
        date_day=str_date[6:8]
    date_from=datetime.strptime(date_year+"-"+date_month+"-"+date_day, "%Y-%m-%d")
    #if len(str_date)!= 8:
        #date = datetime.datetime.now()
       # str_date=str(date.year)+str(date.month)+str(date.day)
    #print(f"the str_date is {str_date}")
    #start_time_query=datetime.now()   
    query = Query(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='191',
            subfields={'b': re.compile('^S\/')}
        ) 
    )
    dict_query= {"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)},"191.subfields.value":{"$regex":"^S\/"}}
    export_fields={'089':1,'091':1,'191': 1,'239':1,'245':1,'249':1,'260':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'630':1,'650':1,'651':1,'710':1,'981':1,'989':1,'991':1,'992':1,'993':1,'996':1}
    bibset = BibSet.from_query(dict_query, projection=export_fields, skip=skp, limit=limt)
    out_list=[('089','b'),('091','a'),('191','a'),('191','b'),('191','c'),('191','9'),('239','a'),('245','a'),('245','b'),('245','c'),('249','a'),('260','a'),('260','b'),('260','c'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('630','a'),('650','a'),('651','a'),('710','a'),('981','a'),('989','a'),('989','b'),('989','c'),('991','a'),('991','b'),('991','c'),('991','d'),('992','a'),('993','a'),('996','a')]
    #print(f"duration for query was {datetime.now()-start_time_query}")
    jsonl=[]
    
    for bib in bibset.records:
        out_dict={}
        #start_time_bib=datetime.now()
        for entry in out_list:
            #start_time_field=datetime.now()
            out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            #print(f"for the field {entry[0]+'__'+entry[1]}")
            #print(f"duration for getting values was {datetime.now()-start_time_field}")
        jsonl.append(out_dict)
        #print(f"for the bib {bib.get_values('650','a')}")
        #print(f"for the bib {bib.get_values('191','a')}")
        #print(f"duration for getting bib values was {datetime.now()-start_time_bib}")
    #print(f"total duration was {datetime.now()-start_time_all}")
    return jsonify(jsonl)

@app.route('/<date>/symbols')
def symbols(date):
    '''
    outputs records in txt format for the date which is provided as a dynamic route in YYYYMMDD or YYYY-MM-DD formats
    e.g. /YYYYMMDD/symbols /YYYY-MM-DD/symbols?skip=n&limit=m
    skip=n URL parameter is used to skip n records. Default is 0.
    limit=m URL parameter is used to limit number of records returned. Default is 50.
    if the date is in wrong format the function returns today's records
    it uses DLX bibset.to_txt serialization function to output MARCXML
    '''
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50
    #print(f"skip is {skp} and limit is {limt}")
    str_date=date.replace('-','')
    #print(f"the original str_date is {str_date}")

    if len(str_date)!= 8:
        date = datetime.datetime.now()
        str_date=str(date.year)+str(date.month)+str(date.day)
    #print(f"the str_date is {str_date}")
    if len(str_date)!= 8:
        ldate = datetime.now()
        str_date=str(ldate.year)+str(ldate.month)+str(ldate.day)
        date_year,date_month, date_day = ldate.year, ldate.month, ldate.day
        date_from=ldate
    else:   
        date_year=str_date[0:4]
        date_month=str_date[4:6]
        date_day=str_date[6:8]
    date_from=datetime.strptime(date_year+"-"+date_month+"-"+date_day, "%Y-%m-%d")
        
    query = Query(
        Condition(
            tag='998',
            subfields={'z': re.compile('^'+str_date)}
        ),
        Condition(
            tag='029',
            subfields={'a':'JN'}
        )
    )
    dict_query= {"updated": {"$gte": date_from, "$lt": date_from+timedelta(days = 1)},"191.subfields.value":{"$regex":"^S\/"}}
    bibset = BibSet.from_query(dict_query, projection={'029':1,'191': 1}, skip=skp, limit=limt)

    str_out=''
    for bib in bibset.records:
        str_out+=bib.to_str()
    return Response(str_out, mimetype='text/plain')


@app.route('/votes/<topic>')
def votes(topic):
    '''
    looks up UNBIS thesaurus labels and returns matching T codes ..
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
    try:   
        yr_from=request.args.get('year_from')
    except:
        yr_from="1980"
    try:
        yr_to=request.args.get('year_to')
    except:
        yr_to='2020'
    try:
        cntry=request.args.get('Country')
    except:
        cntry='CANADA'
    try:
        vt=request.args.get('Vote')
    except:
        vt='A'

    print(f"skip is {skp} and limit is {limt}")
    print(f"year_from is {yr_from} and year_to is {yr_to}") 
    print(f"Country is {cntry}")
    print(f"Vote is {vt}")

    query = Query(
        Condition(
            tag='191',
            subfields={'d': re.compile(str(topic))}
            ),
        Condition(
            tag='191',
            subfields={'a': re.compile('^A')}
            )

    )
    print(query.to_json())
    dict_auth_ids={}
    authset = AuthSet.from_query(query, projection={'001':1,'191':1}, skip=skp, limit=limt)
    for auth in authset:
        dict_auth_ids[auth.get_value('191','a')]=auth.get_value('001')
    #unbis=authset.to_xml()
    #return Response(unbis, mimetype='text/xml')
    #return jsonify(dict_auth_ids)
    dict_bibs={}
    str_bibs=''
    votecountry=''
    for key,value in dict_auth_ids.items():
        #sample_id=int(dict_auth_ids['A/74/251'])
        print(f"the id of {key} is {value}")
        query_bib = Query(
            Condition(
                tag='991',
                subfields={'d':int(value)}
                ),
            Condition(
                tag='989',
                subfields={'a': re.compile(str('Voting Data'))}
                )
        )
        
        print(query_bib.to_json())
        bibset = BibSet.from_query(query_bib, projection={'001':1,'791':1, '967':1}, skip=skp, limit=limt)
        for bib in bibset:
            for field in bib.get_fields('967'):
                votecountry= field.get_value("d")+field.get_value("e")
                #print(f'Country+Vote: {votecountry}')
                if str(votecountry) == str(vt)+str(cntry): # for the entries matching input query parameters using AND logic
                    dict_bibs[bib.get_value('791','a')]=bib.get_value('001')
                    str_bibs=str_bibs+' OR 791:['+bib.get_value('791','a')+']'
    print(str_bibs)   
    return jsonify(dict_bibs)

@app.route('/gadl')
def display_tablega():
    url = 'https://o8mn2cdyp5.execute-api.us-east-1.amazonaws.com/dev/json/?rec_id=23&refresh=true'
    response = requests.get(url)
    data = response.json()
    data1=[]
    dict1={}
    print (type(data))
    for dict in data:
        myorder = ['document_symbol', 'title', 'agenda']
        dict1 = {k: dict[k] for k in myorder}
        data1.append(dict1)

    headers = list(data1[0].keys())
    rows = [list(item.values()) for item in data1]
    return render_template('dl1.html', headers=headers, rows=rows)


@app.route('/scdl')
def display_tablesc():
    url = 'https://o8mn2cdyp5.execute-api.us-east-1.amazonaws.com/dev/json/?rec_id=24&refresh=true'
    response = requests.get(url)
    data = response.json()
    data1=[]
    dict1={}
    print (type(data))
    for dict in data:
        myorder = ['document_symbol', 'title', 'agenda']
        dict1 = {k: dict[k] for k in myorder}
        data1.append(dict1)

    headers = list(data1[0].keys())
    rows = [list(item.values()) for item in data1]
    return render_template('dl1.html', headers=headers, rows=rows)

@app.route('/doc')
def get_pdf():
    
    symbol = request.args.get("symbol")
    lang = request.args.get("lang")
    
    if not symbol or not lang:
        return jsonify({"error": "Missing symbol or lang parameter"}), 400
    
    # Query the database for the document matching criteria
    document = filesColl.find_one({
        "identifiers.value": symbol,
        "languages": lang
    })
    
    if not document or "uri" not in document:
        return jsonify({"error": "PDF not found"}), 404
    
    pdf_uri = document["uri"]
    print(document)
    # If the PDF is stored externally, fetch and serve it
    if pdf_uri.startswith("undl-files.s3.amazonaws.com"):
        pdf_url = document["uri"]
        try:
            response = requests.get("https://"+pdf_url, stream=True)
            if response.status_code != 200:
                return jsonify({"error": "Failed to fetch the PDF"}), 502

            return Response(
                response.iter_content(chunk_size=4096),
                content_type="application/pdf",
                headers={
                    "Content-Disposition": "inline; filename=document.pdf"
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        




        # Supported languages (ordered for display)
LANGUAGES = {
    'ar': 'العربية',
    'zh': '中文',
    'en': 'English',
    'fr': 'Français',
    'ru': 'Русский',
    'es': 'Español'
}
LANGUAGESList =['DE', 'AR', 'FR', 'ES', 'RU', 'ZH', 'EN']

#@app.route("/document1/<path:symbol>")
@app.route("/<lang>/<path:symbol>")
def show_document1(symbol, lang=None):
    lang=lang.upper()
    print(symbol)
    symbol=unquote(symbol)
    print(f"after unquote the symbol is {symbol}")
    cln = Collation(locale='en', strength=2)
    docs = filesColl.find({"identifiers.value": symbol}, collation=cln)
    languages = [''.join(doc.get("languages")) for doc in docs]
    print(languages)
    if lang is None:
        # Find all documents matching the symbol
        docs = filesColl.find({"identifiers.value": symbol})
        languages = [''.join(doc.get("languages")) for doc in docs]
        
        if not languages:
            return "No available languages for this document.", 404
        return render_template("language_selection.html", symbol=symbol, languages=languages, LANGUAGES=LANGUAGES)

    # Look up the specific document for  the given language
    doc = filesColl.find_one({"identifiers.value": symbol, "languages": lang}, collation=cln)
    if not doc or not doc.get("uri"):
        return "Document not found for this language.", 404

    # Fetch and serve the PDF
    symbol=quote(symbol, safe='')
    print(symbol)
    uri = "https://"+doc["uri"]
    response = requests.get(uri)
    if response.status_code == 200:
        return send_file(BytesIO(response.content), download_name=f"{symbol}_{lang}.pdf", mimetype='application/pdf')
    else:
        return "Unable to fetch PDF", 502


@app.route("/document2/<path:symbol>")
#@app.route("/document1/<path:lang>/<path:symbol>/")
def show_document2(symbol, lang=None):
    print(symbol)
    docs = filesColl.find({"identifiers.value": symbol})
    languages = [''.join(doc.get("languages")) for doc in docs]
    print(languages)
    if lang is None:
        # Find all documents matching the symbol
        docs = filesColl.find({"identifiers.value": symbol})
        languages = [''.join(doc.get("languages")) for doc in docs]
        
        if not languages:
            return "No available languages for this document.", 404
        return render_template("language_selection.html", symbol=symbol, languages=languages, LANGUAGES=LANGUAGES)

    # Look up the specific document for the given language
    doc = filesColl.find_one({"identifiers.value": symbol, "languages": languages})
    if not doc or not doc.get("uri"):
        return "Document not found for this language.", 404

    # Fetch and serve the PDF
    uri = "https://"+doc["uri"]
    response = requests.get(uri)
    if response.status_code == 200:
        return send_file(BytesIO(response.content), download_name=f"{symbol}_{lang}.pdf", mimetype='application/pdf')
    else:
        return "Unable to fetch PDF", 502
    

@app.route('/list')
def show_list():
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50 
    print(f"skip is {skp} and limit is {limt}")
    
    tag=request.args.get('tag')
    query1=request.args.get('query')
    #query = Query.from_string("symbol:"+'"'+path+'"') # Dataset-search_query
    print(f"{tag}:{query1}")
    query1 = Query.from_string(f"{tag}:{query1}") # Dataset-search_query f"191__a:'{path}'""
    sort_field = request.args.get('sort', '269')  # default sort field
    sort_direction = request.args.get('dir', 'desc').lower()
    #query = QueryDocument(  
     #   Condition(
     #       tag='191',
     #       #subfields={'a': re.compile('^'+path+'$')}
     #       subfields={'a': path}
     #   )
    #)
    #print(f" the imp query is  -- {query.to_json()}")
    #export_fields={'089':1,'091':1,'191': 1,'239':1,'245':1,'249':1,'260':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'630:1,''650':1,'651':1,'710':1,'981':1,'989':1,'991':1,'992':1,'993':1,'996':1}
    sort_direction = -1 if sort_direction == 'desc' else 1
    bibset = BibSet.from_query(query1,sort={sort_field:sort_direction},skip=skp, limit=limt)
    out_list=[('001',''),('089','b'),('091','a'),('191','a'),('191','b'),('191','c'),('191','9'),('239','a'),('245','a'),('245','b'),('245','c'),('249','a'),('260','a'),('260','b'),('260','c'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('630','a'),('650','a'),('651','a'),('710','a'),('981','a'),('989','a'),('989','b'),('989','c'),('991','a'),('991','b'),('991','c'),('991','d'),('992','a'),('993','a'),('996','a')]
    #print(f"duration for query was {datetime.now()-start_time_query}")
    #print(f"time for query is {time.time()-ts2}")
    jsonl=[]
    #print(f"time for query is {time.time()-ts2}")
    for bib in bibset.records:
        
        out_dict={} 
        #start_time_bib=datetime.now()
        for entry in out_list:
            #start_time_field=datetime.now()
            if entry[1]=='':
                out_dict[entry[0]]=bib.id
            else:
                out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            #print(f"for the field {entry[0]+'__'+entry[1]}")
            #print(f"duration for getting values was {datetime.now()-start_time_field}")
            



        jsonl.append(out_dict)
        #print(f"for the bib {bib.get_values('191','a')}")
        #print(f"duration for getting bib values was {datetime.now()-start_time_bib}")
    #print(f"total duration was {datetime.now()-start_time_all}")
    return jsonify(jsonl)

@app.route('/list30')
def show_list30():
    try:
        skp=int(request.args.get('skip'))
    except:
        skp=0
    try:
        limt=int(request.args.get('limit'))
    except:
        limt=50 
    print(f"skip is {skp} and limit is {limt}")
    
    tag=request.args.get('tag')
    query=request.args.get('query')
    sort_field = request.args.get('sort', '269')  # default sort field
    sort_direction = request.args.get('dir', 'desc').lower()
    days=request.args.get('days', '30')
    last=request.args.get('last', 'created')  # default to created date
    #query = QueryDocument(  
     #   Condition(
     #       tag='191',
     #       #subfields={'a': re.compile('^'+path+'$')}
     #       subfields={'a': path}
     #   )
    #)
    #print(f" the imp query is  -- {query.to_json()}")
    #export_fields={'089':1,'091':1,'191': 1,'239':1,'245':1,'249':1,'260':1,'269':1,'300':1,'500':1,'515':1,'520':1,'596':1,'598':1,'610':1,'611':1,'630:1,''650':1,'651':1,'710':1,'981':1,'989':1,'991':1,'992':1,'993':1,'996':1}
    # filter to records updated in the last 30 days
    date_threshold = datetime.utcnow() - timedelta(days=int(days))

    # Build a Mongo-style dict query that includes the updated threshold.
    dict_query = {last: {"$gte": date_threshold}}

    # If query param looks like tag__subfield:value (API style), parse and add to dict_query
    if query and '__' in query and ':' in query:
        try:
            tag_subfield, val = query.split(':', 1)
            tag, subf = tag_subfield.split('__', 1)
            val = val.strip().strip('"\'')
            #print([hex(ord(c)) for c in val])
            # support trailing wildcard '*'
            if val.endswith('*'):
                #pattern = re.compile(r'^' + re.escape(val[:-1]))
                normal = val.replace('⁄', '/')
                pattern = re.compile(r'^' + re.escape(normal[:-1]))
                print(f"pattern is {pattern}")
                dict_query[f"{tag}.subfields.value"] = pattern
            else:
                dict_query[f"{tag}.subfields.value"] = val
        except Exception:
            # fall back to leaving dict_query as-is (only date filter)
            pass

    # convert sort direction to pymongo sort order
    sort_dir = -1 if sort_direction == 'desc' else 1
    print(f" the dict query is  -- {dict_query}")
    bibset = BibSet.from_query(dict_query, sort={sort_field: sort_dir}, skip=skp, limit=limt)
    out_list=[('001',''),('089','b'),('091','a'),('191','a'),('191','b'),('191','c'),('191','9'),('239','a'),('245','a'),('245','b'),('245','c'),('249','a'),('260','a'),('260','b'),('260','c'),('269','a'),('300','a'),('500','a'),('515','a'),('520','a'),('596','a'),('598','a'),('610','a'),('611','a'),('630','a'),('650','a'),('651','a'),('710','a'),('791','a'),('981','a'),('989','a'),('989','b'),('989','c'),('991','a'),('991','b'),('991','c'),('991','d'),('992','a'),('993','a'),('996','a')]
    #print(f"duration for query was {datetime.now()-start_time_query}")
    #print(f"time for query is {time.time()-ts2}")
    jsonl=[]
    #print(f"time for query is {time.time()-ts2}")
    for bib in bibset.records:
        
        out_dict={} 
        #start_time_bib=datetime.now()
        for entry in out_list:
            #start_time_field=datetime.now()
            if entry[1]=='':
                out_dict[entry[0]]=bib.id
            else:
                out_dict[entry[0]+'__'+entry[1]]=bib.get_values(entry[0],entry[1])
            #print(f"for the field {entry[0]+'__'+entry[1]}")
            #print(f"duration for getting values was {datetime.now()-start_time_field}")
            



        jsonl.append(out_dict)
        #print(f"for the bib {bib.get_values('191','a')}")
        #print(f"duration for getting bib values was {datetime.now()-start_time_bib}")
    #print(f"total duration was {datetime.now()-start_time_all}")
    return jsonify(jsonl)


@app.route('/multi_query')
def show_multi_query():
    """
    Accepts multiple tag:query pairs as query parameters.
    Example: /multi_list?tag1=191&query1=SR.1139&tag2=245&query2=Committee
    Returns records matching all tag:query pairs (AND logic).
    """
    try:
        skp = int(request.args.get('skip', 0))
    except Exception:
        skp = 0
    try:
        limt = int(request.args.get('limit', 50))
    except Exception:
        limt = 50

    # Collect all tag:query pairs from the request
    tags = []
    queries = []
    for key in request.args:
        if key.startswith('tag'):
            idx = key[3:]
            tag = request.args.get(key)
            query_val = request.args.get(f'query{idx}')
            if tag and query_val:
                tags.append(tag)
                queries.append(query_val)

    # Build Query object with AND logic
    conditions = []
    for tag, val in zip(tags, queries):
        conditions.append(Condition(tag=tag, subfields={'a': val}))
    if not conditions:
        return jsonify({"error": "No tag:query pairs provided"}), 400

    query = Query(*conditions)
    bibset = BibSet.from_query(query, skip=skp, limit=limt)
    out_list = [
        ('089', 'b'), ('091', 'a'), ('191', 'a'), ('191', 'b'), ('191', 'c'), ('191', '9'),
        ('239', 'a'), ('245', 'a'), ('245', 'b'), ('245', 'c'), ('249', 'a'), ('260', 'a'),
        ('260', 'b'), ('260', 'c'), ('269', 'a'), ('300', 'a'), ('500', 'a'), ('515', 'a'),
        ('520', 'a'), ('596', 'a'), ('598', 'a'), ('610', 'a'), ('611', 'a'), ('630', 'a'),
        ('650', 'a'), ('651', 'a'), ('710', 'a'), ('830', 'a'), ('981', 'a'), ('989', 'a'), ('989', 'b'),
        ('989', 'c'), ('991', 'a'), ('991', 'b'), ('991', 'c'), ('991', 'd'), ('992', 'a'),
        ('993', 'a'), ('996', 'a')
    ]
    jsonl = []
    for bib in bibset.records:
        out_dict = {}
        for entry in out_list:
            out_dict[entry[0] + '__' + entry[1]] = bib.get_values(entry[0], entry[1])
        jsonl.append(out_dict)
    return jsonify(jsonl)

@app.route('/multi_query_partial')
def show_multi_query_partial():
    """
    Accepts multiple tag:query pairs as query parameters.
    Example: /multi_list?tag1=191&query1=SR.1139&tag2=245&query2=Committee
    Returns records matching all tag:query pairs (AND logic).
    Partial queries are supported: e.g. query1=E/1981 will match E/1981/55.
    """
    import re

    try:
        skp = int(request.args.get('skip', 0))
    except Exception:
        skp = 0
    try:
        limt = int(request.args.get('limit', 50))
    except Exception:
        limt = 50

    # Collect all tag:query pairs from the request
    tags = []
    queries = []
    for key in request.args:
        if key.startswith('tag'):
            idx = key[3:]
            tag = request.args.get(key)
            query_val = request.args.get(f'query{idx}')
            if tag and query_val:
                tags.append(tag)
                queries.append(query_val)

    # Build Query object with AND logic, using regex for partial match
    conditions = []
    for tag, val in zip(tags, queries):
        # Use regex to match any value that starts with the query string
        regex = re.compile(f'{re.escape(val)}')
        conditions.append(Condition(tag=tag, subfields={'a': regex}))
    if not conditions:
        return jsonify({"error": "No tag:query pairs provided"}), 400

    query = Query(*conditions)
    bibset = BibSet.from_query(query, skip=skp, limit=limt)
    out_list = [
        ('089', 'b'), ('091', 'a'), ('191', 'a'), ('191', 'b'), ('191', 'c'), ('191', '9'),
        ('239', 'a'), ('245', 'a'), ('245', 'b'), ('245', 'c'), ('249', 'a'), ('260', 'a'),
        ('260', 'b'), ('260', 'c'), ('269', 'a'), ('300', 'a'), ('500', 'a'), ('515', 'a'),
        ('520', 'a'), ('596', 'a'), ('598', 'a'), ('610', 'a'), ('611', 'a'), ('630', 'a'),
        ('650', 'a'), ('651', 'a'), ('710', 'a'), ('830', 'a'), ('981', 'a'), ('989', 'a'), ('989', 'b'),
        ('989', 'c'), ('991', 'a'), ('991', 'b'), ('991', 'c'), ('991', 'd'), ('992', 'a'),
        ('993', 'a'), ('996', 'a')
    ]
    jsonl = []
    for bib in bibset.records:
        out_dict = {}
        for entry in out_list:
            out_dict[entry[0] + '__' + entry[1]] = bib.get_values(entry[0], entry[1])
        jsonl.append(out_dict)
    return jsonify(jsonl)



import jwt
from functools import wraps
from flask import request, jsonify

# Secret key for JWT (should be kept safe in production)
JWT_SECRET = "ODS-eXport"
JWT_ALGORITHM = "HS256"

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("access_token")
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated_function

from werkzeug.security import check_password_hash

@app.route('/login', methods=['POST', 'GET'])
def login():
    username = os.environ.get("lib_user")
    password = os.environ.get("lib_password")
    JWT_SECRET ="your-jwt-secret"
    if not username or not password:
        return jsonify({"error": "lib_user and lib_password env. vars required"}), 400
    aws_client=client = boto3.client('ssm')
    uat_connect_string=aws_client.get_parameter(Name='uatISSU-admin-connect-string')['Parameter']['Value']
    client = MongoClient(uat_connect_string)
    db = client["DynamicListings"]  # use your actual database name
    users_collection = db["dl_users_collection"]
    user = users_collection.find_one({"email": username})
    if not user or not check_password_hash(user.get("password", ""), password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    #jwt_secret is stored for accessing custom secret per application
    JWT_SECRET=user.get("ods_export_jwt_secret", JWT_SECRET)
    # Issue JWT token as before...
    import jwt, datetime
    from flask import make_response
    payload = {
        "user": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    resp = make_response(jsonify({"message": "Logged in"}))
    resp.set_cookie(
        "access_token", 
        token, 
        httponly=True,  # JS cannot read it
        secure=True,    # send only over HTTPS
        samesite="Strict"
    )
    return resp





@app.route('/multi_query_partial_subfield')
#@jwt_required
def show_multi_query_partial_subfield():
    """
    Accepts multiple tag:query pairs as query parameters.
    Example: /multi_query_partial_subfield?tag1=191&query1=E/1981&subfield1=a&tag2=245&query2=Committee&subfield2=b
    Returns records matching all tag:query pairs (AND logic).
    Partial queries are supported: e.g. query1=E/1981 will match E/1981/55.
    You can specify subfieldN for each tagN/queryN (defaults to 'a' if not provided).
    """
    import re

    try:
        skp = int(request.args.get('skip', 0))
    except Exception:
        skp = 0
    try:
        limt = int(request.args.get('limit', 50))
    except Exception:
        limt = 50

    # Collect all tag:query pairs and subfields from the request
    tags = []
    queries = []
    subfields = []
    for key in request.args:
        if key.startswith('tag'):
            idx = key[3:]
            tag = request.args.get(key)
            query_val = request.args.get(f'query{idx}')
            subfield_val = request.args.get(f'subfield{idx}', 'a')
            if tag and query_val:
                tags.append(tag)
                queries.append(query_val)
                subfields.append(subfield_val)

    # Build Query object with AND logic, using regex for partial match and any subfield
    conditions = []
    for tag, val, subf in zip(tags, queries, subfields):
        regex = re.compile(f'{re.escape(val)}')
        conditions.append(Condition(tag=tag, subfields={subf: regex}))
    if not conditions:
        return jsonify({"error": "No tag:query pairs provided"}), 400

    query = Query(*conditions)
    print(query.to_json())
    bibset = BibSet.from_query(query, skip=skp, limit=limt)
    out_list = [
        ('089', 'b'), ('091', 'a'), ('191', 'a'), ('191', 'b'), ('191', 'c'), ('191', '9'),
        ('239', 'a'), ('245', 'a'), ('245', 'b'), ('245', 'c'), ('249', 'a'), ('260', 'a'),
        ('260', 'b'), ('260', 'c'), ('269', 'a'), ('300', 'a'), ('500', 'a'), ('515', 'a'),
        ('520', 'a'), ('596', 'a'), ('598', 'a'), ('610', 'a'), ('611', 'a'), ('630', 'a'),
        ('650', 'a'), ('651', 'a'), ('710', 'a'), ('830', 'a'), ('981', 'a'), ('989', 'a'), ('989', 'b'),
        ('989', 'c'), ('991', 'a'), ('991', 'b'), ('991', 'c'), ('991', 'd'), ('992', 'a'),
        ('993', 'a'), ('996', 'a'),('001','')
    ]
    jsonl = []
    for bib in bibset.records:
        out_dict = {}
        for entry in out_list:
            if entry[1]!='':
                out_dict[entry[0] + '__' + entry[1]] = bib.get_values(entry[0], entry[1])
            else:
                out_dict[entry[0]] = bib.id
        jsonl.append(out_dict)
    return jsonify(jsonl)
