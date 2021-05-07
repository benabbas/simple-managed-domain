# mlytics MANAGED DOMAINS
## Introduction

This web application built to monitor the domain names managed by mlytics. The application will automatically check the expiration date each domain in the database everyday and report to mlytics zabbix server if the domain is going to expired. 

The application using python-Flask with the requirements as follow:
```gherkin=
flask
flask_session
flask_sqlalchemy
datetime
dateutil.tz
whois
json
pandas
blueprint
```

#### Interface
![](https://i.imgur.com/cxbPNRt.png)

#### Functions 
**Last Update (2021/05/04)**
* Reject the adding when the domain already exist
* Give a warning when the domain 

API
---

* Get all domain list: 
`curl -s https://www.bentech.site/apitest/all | jq -r` 

* Get all domain that will be expired in 60 days: 
`curl -s https://www.bentech.site/apitest/expired | jq -r` 

* Add new domain:
`curl -s https://www.bentech.site/apitest/update?domain=test.com`

* Force Update:
    * Force add domain 
`curl -s https://www.bentech.site/apitest/update/force?domain={value}`

    * days_left 
`curl -s https://www.bentech.site/apitest/update/force?id={value}&days_left={value}`

    * icp 
`curl -s https://www.bentech.site/apitest/update/force?id={}&icp={value}`

    * registrar 
`curl -s https://www.bentech.site/apitest/update/force?id={}&registrar={value}`

    * expired 
`curl -s https://www.bentech.site/apitest/update/force?id={}&expired={value}`

Manual Update
---

This is to manually check and update Expired Date and Days Left. 
Command: `$python expired_updator`
```gherkin=
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 17:10:57 2021

@author: ben
"""

import requests
import json
import pandas as pd

url = 'http://www.bentech.site/apitest/all'

resp=requests.get(url)
    # read the text object string
try:
    resp_text = json.loads(resp.text)
except:
    resp_text = resp.text
    
data = pd.DataFrame.from_dict(resp_text)

def update(data_id, data_domain):
    update_url="http://www.bentech.site/apitest/update?id="+data_id+"&domain="+data_domain+"&all=0"
    resp_update=requests.get(update_url)
    print(resp_update.text)

for row in data.index:
    data_id=str(data['id'][row])
    data_domain=data['domain'][row]
    update(data_id, data_domain)
```
**The Code below to change Registrar Name record**
```gherkin=
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 30 17:10:57 2021

@author: ben
"""

import requests
import json
import pandas as pd

url = 'http://www.bentech.site/apitest/all'

resp=requests.get(url)
    # read the text object string
try:
    resp_text = json.loads(resp.text)
except:
    resp_text = resp.text
    
data = pd.DataFrame.from_dict(resp_text)

def update(data_id, registrar):
    data_id = str(data_id)
    update_url="https://www.bentech.site/apitest/update/force?id="+data_id+"&registrar="+registrar
    resp_update=requests.get(update_url)
    return resp_update.text

for index, row in data.iterrows():
    if "NameBright" in row['registrar'] or "DropCatch.com" in row['registrar']:
        update(row['id'], "NameBright")
    if "ALIBABA.COM" in row['registrar']:
        update(row['id'], "ALIBABA.COM")
```

Zabbix Alert
---
Script to get the domain names that is going to expired within 60 days
```gherkin=bash
#!/bin/bash

for i in $(curl "https://www.bentech.site/apitest/expired" -s | jq -r '.[]| {domain: .domain, days_left: .days_left}' | tr -d '{' | xargs | sed 's/}/\n/g' | sed '/^$/d'| sed 's/ //g')
do
        echo $i | sed 's/domain://g' | sed 's/days_left://g' | awk -F ',' '{print $1" ("$2" days),"}'
done
```

![](https://i.imgur.com/cMzHRQt.png)


**Triggered:** 
* If the List of Managed Domain-Expired is not empty then the alert will appear

**Update Interval:** Only updated on Monday at 17.00 GMT+8

![](https://i.imgur.com/FPid6ER.png)
![](https://i.imgur.com/ts6qdJD.png)

**Acknowledge and close the alert information:**
![](https://i.imgur.com/uK8wKey.png)

###### tags: `mlytics` `managed_domain`
