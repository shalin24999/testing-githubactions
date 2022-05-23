#this script will only work for apps made with openAPI

import requests
import json
from requests.auth import HTTPBasicAuth
import pprint as pp
import time
import os
import json

#Libs and auth
from googleapiclient.discovery import build
from google.oauth2 import service_account

#Add shuffle-sandbox service account and token
username = os.environ['USER_NAME']
token = os.environ['TOKEN']
service_account_sandbox = os.environ['SERVICE_ACCOUNT_SANDBOX']
sandbox_token = os.environ['SANDBOX_USER_TOKEN']
pr_number = os.environ['PR_NUMBER']

#Creds for cloud function API
json_account_info = json.loads(fr'{service_account_sandbox}')
print(json_account_info)
credentials = service_account.Credentials.from_service_account_info(json_account_info)
service = build('cloudfunctions', 'v1',credentials=credentials)
locations = service.projects().locations().list(name="projects/shuffle-sandbox-337810").execute()

###################################################################################################################

#Get open API specs
def get_files(owner_name:str, repo_name:str, pr_number:int):
    file_link = []
    files_url = f'https://api.github.com/repos/{owner_name}/{repo_name}/pulls/{pr_number}/files'
    response = requests.get(files_url,auth=HTTPBasicAuth(username, token))
    data = response.json()
    print(data)
    for i in data:
        if (i['filename'].split('.')[-1] == 'json' or i['filename'].split('.')[-1] == 'yaml' or i['filename'].split('.')[-1] == 'yml') and (i['status'] == 'added' or i['status'] == 'modified'):
            file_link.append(i['raw_url'])
    return file_link

def get_specs(spec_url,sandbox_token):
    headers = {
        "Authorization":f"Bearer {sandbox_token}",
        "Content-Type":"application/json"
    }
    response = requests.post("https://sandbox.shuffler.io/api/v1/get_openapi_uri",headers=headers,data=spec_url)
    return response.text

#validate app and get app_id
def validate_app(app_specs, sandbox_token):
    validate_url = "https://sandbox.shuffler.io/api/v1/validate_openapi"
    headers = {
        "Authorization":f"Bearer {sandbox_token}",
        "Content-Type":"application/json"
    }
    validate_app = requests.post(validate_url,headers=headers,data=app_specs)
    print('App validation -> ',validate_app.status_code)
    if not validate_app.raise_for_status():
        return validate_app.json()['id']
    return 'App validation failed. make sure yaml or json file valid'
    

#Getting parsed data
def parsed_data(app_id, sandbox_token):
    headers = {
        "Authorization":f"Bearer {sandbox_token}",
        "Content-Type":"application/json"
    }
    full_data = f"https://sandbox.shuffler.io/api/v1/get_openapi/{str(app_id)}"
    save = requests.get(full_data,headers=headers)
    print('sending full data ->',save.status_code)
    if not save.raise_for_status():
        return save.json()['body']
    return 'File parsing failed.'

#Verify app
def verify_app(app_data, sandbox_token):
    verify_app_url = "https://sandbox.shuffler.io/api/v1/verify_openapi"
    headers = {
        "Authorization":f"Bearer {sandbox_token}",
        "Content-Type":"application/json"
    }
    deploy_app = requests.post(verify_app_url, headers = headers , data=app_data)
    print("app verification -> ",deploy_app.status_code)
    if not deploy_app.raise_for_status():
        return deploy_app.json()['id'] 
    return 'Unable to verify app !!'

#Now we need to make sure that cloud function runs properly once its deployed

#It takes some time for cloud function to get deployed so we'll have to wait for it to finish deploying
def get_function_url(function_id):
    ######################### fix this for sandbox ########################
    ''' This function will return cloud function url of an open api APP. '''
    functions = service.projects().locations().functions().list(parent="projects/shuffle-sandbox-337810/locations/-").execute()
    for i in functions.get('functions'):
        name = i.get('name').split('-')
        if function_id == name[-1]:
            return i.get('httpsTrigger').get('url')
    raise Exception('Cloud function not found')

#Making API call to deployed cloud function
def test_cloud_function(function_url):
    headers = {
        "Content-Type":"application/json"
    }
    data = {
        "test":"ok"
    }
    response = requests.post(function_url,json=data)
    if not response.raise_for_status():
        return f'Function deployed successfully ! {response.text}'

def wrapper_func():
    specs_url = get_files("shalin24999","testing-githubactions",pr_number)
    for i in specs_url:
        specs = get_specs(i,sandbox_token)
        app_id = validate_app(specs,sandbox_token)
        print(app_id)
        app_data = parsed_data(app_id,sandbox_token)
        function_id = verify_app(app_data,sandbox_token)
        print("Waiting for cloud function to be deployed....")
        time.sleep(90)
        function_url = get_function_url(function_id)
        print(test_cloud_function(function_url))
wrapper_func()


