from flask import Flask, render_template, request, abort, jsonify, Response, url_for
from requests import get
from bson.objectid import ObjectId
from .config import Config
import boto3, re, time, os, pymongo

# Initialize your application.
app = Flask(__name__)
collection = Config.DB.bibs

# Define any classes you want to use here, or you could put
# them in other files and import.
return_data=""
# And start building your routes.
@app.route('/')
def index():
    return(render_template('index.html', data=return_data))
