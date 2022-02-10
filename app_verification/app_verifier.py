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
import google.auth

username = os.environ['USER_NAME']
token = os.environ['TOKEN']
service_account_shuffler = os.environ['SERVICE_ACCOUNT_SHUFFLER']
#print(type(service_account_shuffler.encode('unicode_escape')))
pr_number = os.environ['PR_NUMBER']
#credentials, _ = google.auth.default()

#Creds for cloud function API
#json_account_info = json.loads(service_account_shuffler)
#credentials = service_account.Credentials.from_service_account_file('cred.json')
service = build('cloudfunctions', 'v1',credentials=fr'{service_account_shuffler}')
locations = service.projects().locations().list(name="projects/shuffler").execute()

###################################################################################################################

#Get open API specs
def get_files(owner_name:str, repo_name:str, pr_number:int):
    file_link = []
    files_url = f'https://api.github.com/repos/{owner_name}/{repo_name}/pulls/{pr_number}/files'
    response = requests.get(files_url,auth=HTTPBasicAuth(username, token))
    data = response.json()
    for i in data:
        if (i['filename'].split('.')[-1] == 'json' or i['filename'].split('.')[-1] == 'yaml' or i['filename'].split('.')[-1] == 'yml') and (i['status'] == 'added' or i['status'] == 'modified'):
            file_link.append(i['raw_url'])
    return file_link

def get_specs(spec_url,shuffle_token="3fd8c33c-050f-4de4-ae44-e2f9d9d884ac"):
    headers = {
        "Authorization":f"Bearer {shuffle_token}",
        "Content-Type":"application/json"
    }
    response = requests.post("https://shuffler.io/api/v1/get_openapi_uri",headers=headers,data=spec_url)
    return response.text

app_specs = get_specs("https://raw.githubusercontent.com/Shuffle/openapi-apps/master/jira.yaml")

#validate app and get app_id
def validate_app(app_specs, shuffle_token="3fd8c33c-050f-4de4-ae44-e2f9d9d884ac"):
    validate_url = "https://shuffler.io/api/v1/validate_openapi"
    headers = {
        "Authorization":f"Bearer {shuffle_token}",
        "Content-Type":"application/json"
    }
    validate_app = requests.post(validate_url,headers=headers,data=app_specs)
    print('App validation -> ',validate_app.status_code)
    if not validate_app.raise_for_status():
        return validate_app.json()['id']
    return 'Error'
    

#Getting parsed data
def parsed_data(app_id, shuffle_token="3fd8c33c-050f-4de4-ae44-e2f9d9d884ac"):
    headers = {
        "Authorization":f"Bearer {shuffle_token}",
        "Content-Type":"application/json"
    }
    full_data = f"https://shuffler.io/api/v1/get_openapi/{str(app_id)}"
    save = requests.get(full_data,headers=headers)
    print('sending full data ->',save.status_code)
    if not save.raise_for_status():
        return save.json()['body']

#Verify app
def verify_app(app_data, shuffle_token="3fd8c33c-050f-4de4-ae44-e2f9d9d884ac"):
    verify_app_url = "https://shuffler.io/api/v1/verify_openapi"
    headers = {
        "Authorization":f"Bearer {shuffle_token}",
        "Content-Type":"application/json"
    }
    deploy_app = requests.post(verify_app_url, headers = headers , data=app_data)
    print("app verification -> ",deploy_app.status_code)
    if not deploy_app.raise_for_status():
        return deploy_app.json()['id'] 

#Now we need to make sure that cloud function runs properly once its deployed

#It takes some time for cloud function to get deployed so we'll have to wait for it to finish deploying
def get_function_url(function_id):
    ''' This function will return cloud function url of open api APP. '''
    functions = service.projects().locations().functions().list(parent="projects/shuffler/locations/-").execute()
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
    return (response.status_code, response.text())

def wrapper_func():
    specs_url = get_files("shalin24999","testing-githubactions",pr_number)
    for i in specs_url:
        specs = get_specs(i)
        app_id = validate_app(specs)
        app_data = parsed_data(app_id)
        function_id = verify_app(app_data)
        print("Waiting for cloud function to be deployed....")
        time.sleep(120)
        function_url = get_function_url(function_id)
        print(test_cloud_function(function_url))
#wrapper_func()
print(get_files("shalin24999", "testing-githubactions", pr_number))


