from dlx import DB, Bib, Auth
import boto3

'''
This is your application configuration file. Use it to set your various configurations,
but DO NOT put credentials in this file because this file may be checked in to a public
repository.

Acceptable means of storing/accessing credentials:
  - AWS Parameter Store, e.g.:

        import boto3
        client = boto3.client('ssm')
        username = client.get_parameter(Name='username')['Parameter']['Value']
        password = client.get_parameter(Name='password')['Parameter']['Value']

    Obviously you need to have the desired parameters already stored in Parameter Store, and you
    should have the awscli installed and configured with a key id and secret key supplied by AWS 
    or your AWS administrator.

  - Environment variables:

        import os
        username = os.environ.get('username')
        password = os.environ.get('password')

Note that if you use environment variables and plan to incorporate a CI/CD pipeline, e.g., with 
Travis CI, you will need to make sure your CI environment has the appropriate variables defined
and stored.
'''

class Config(object):
    # how many results per page
    RPP = 10

    client = boto3.client('ssm')
    connect_string = client.get_parameter(Name='connect-string')['Parameter']['Value']

    DB = DB.connect(connect_string)
    
class ProductionConfig(Config):
    DEBUG = False
    
class DevelopmentConfig(Config):
    # Provide overrides for production settings here.
    DEBUG = True
