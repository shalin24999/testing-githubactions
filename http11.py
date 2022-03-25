import time
import json
import ast
import random
import socket
# import uncurl
import asyncio
import requests
import subprocess
def checkverify(verify):
        if verify.lower().strip() == "false":
            return False
        elif verify == None:
            return False
        elif verify:
            return True
        elif not verify:
            return False
        else:
            return True 

def splitheaders(headers):
        parsed_headers = {}
        if headers:
            split_headers = headers.split("\n") 
            logger.info(split_headers)
            for header in split_headers:
                if ": " in header:
                    splititem = ": "
                elif ":" in header:
                    splititem = ":"
                elif "= " in header:
                    splititem = "= "
                elif "=" in header:
                    splititem = "="
                else:
                    logger.info("Skipping header %s as its invalid" % header)
                    continue

                splitheader = header.split(splititem)
                if len(splitheader) == 2:
                    parsed_headers[splitheader[0]] = splitheader[1]
                else:
                    logger.info("Skipping header %s with split %s cus only one item" % (header, splititem))
                    continue

        return parsed_headers
def fix_url(url):
        # Random bugs seen by users
        if "hhttp" in url:
            url = url.replace("hhttp", "http")

        if "http:/" in url and not "http://" in url:
            url = url.replace("http:/", "http://", -1)
        if "https:/" in url and not "https://" in url:
            url = url.replace("https:/", "https://", -1)
        if "http:///" in url:
            url = url.replace("http:///", "http://", -1)
        if "https:///" in url:
            url = url.replace("https:///", "https://", -1)
        if not "http://" in url and not "http" in url:
            url = f"http://{url}" 

        return url
def GET(url, headers="", username="", password="", verify="True", http_proxy="", https_proxy="", timeout=5, to_file=False):
        url = fix_url(url)

        parsed_headers = splitheaders(headers)
        parsed_headers["User-Agent"] = "Shuffle Automation"
        verify = checkverify(verify)
        proxies = None
        if http_proxy: 
            proxies["http"] = http_proxy
        if https_proxy: 
            proxies["https"] = https_proxy

        auth=None
        if username or password:
            auth = requests.auth.HTTPBasicAuth(username, password)

        if not timeout:
            timeout = 5
        if timeout:
            timeout = int(timeout)

        if to_file == "true":
            to_file = True
        else:
            to_file = False 

        request = requests.get(url, headers=parsed_headers, auth=auth, verify=verify, proxies=proxies, timeout=timeout)
        if not to_file:
            return prepare_response(request)
        
        return return_file(request.text)

temp = GET("https://stackoverflow.com")
print(type(temp))
print(temp)
