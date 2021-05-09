#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 17:10:57 2021

@author: ben
"""

import requests
import json
import pandas as pd
import logging
import time

url = 'http://127.0.0.1:80/apitest/all'

resp=requests.get(url)
    # read the text object string
try:
    resp_text = json.loads(resp.text)
except:
    resp_text = resp.text
    
data = pd.DataFrame.from_dict(resp_text)

def update(data_id, data_domain, result):
    update_url="http://127.0.0.1:80/apitest/update?id="+data_id+"&domain="+data_domain+"&all=0"
    resp_update=requests.get(update_url)
    result = result.append(resp_update.text)
    return resp_update.text, result

def logging_res(result):
    logging.basicConfig(filename='myapp.log', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    total_domain = len(result)
    total_success = result.count('success')
    logging.info('Total Domain: '+str(total_domain)+', Success: '+str(total_success))

if __name__ == '__main__':
    while True:
        result = []
        for row in data.index:
            data_id=str(data['id'][row])
            data_domain=data['domain'][row]
            update(data_id, data_domain, result)
        logging_res(result)
        time.sleep(43200)
