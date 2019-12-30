# Basic Flask Template for Zappa Deployment
This template is an empty Flask application you can use to build your own application. It assumes you are going to use Git for source version control and deploy to Amazon's API Gateway and Lambda services. What it does not assume is that you have all the resouces already setup for use.

To use this template, you will want to clone, fork, or otherwise copy the code to your own development space. Each file included here contains brief comments on how to use it, but much of this is also covered here in the README.

First, let's look at the application structure. This README assumes you've named your application "sample". You can rename the application by moving the "sample" folder to something you've named, but it's really a superficial item and is unnecessary. 
```
.
+-- sample/
|     +-- static/
|     +-- templates/
|     | +-- base.html
|     | +-- index.html
|     +-- __init__.py
|     +-- app.py
|     +-- config.default.py
|     +-- config.py
+-- .gitignore
+-- README.md
+-- requirements.txt
+-- zappa_settings.default.json
+-- zappa_settings.json
```
These are the minimum components necessary to build a basic Flask application that is deployable to AWS Lambda/API Gateway. It also defaults toward connecting to a MongoDB database, the details of which you enter into your configuration file.

To run this after downloading it, you will have to take the following steps:

1. Install your virtual environment, e.g.: `virtualenv venv`
2. Activate your virtual environtment. On Windows: `.\venv\Scripts\activate.ps1` or `.\venv\Scripts\activate.bat`, and on Linux: `./venv/bin/activate`
3. Install your dependencies from the included requirements file: `pip install -r requirements.txt`
4. Copy sample/config.default.py to sample/config.py and edit it to include your database connection details.
5. Set your local FLASK_APP environment variable. On Windows PowerShell: `$env:FLASK_APP="sample.app"`, and on Linux: `export FLASK_APP="sample.app"`
6. Run the application: `flask run`

Deploying it requires that you already have prepared your Amazon account for all of the things Zappa will need. If you have a root account with Amazon, this is easier, but otherwise you will have to set a number of permissions in your IAM settings. Once you have that in place, though, deployment to Zappa is as easy as copying your zappa_settings.default.json file to zappa_settings.json and editing it to reflect your AWS environment. Then you can run, e.g., `zappa deploy dev` to deploy to your development stage.
