from hashlib import md5

import requests
from elasticsearch import Elasticsearch, TransportError


def getAuthVtiger():
    global url, values, response
    # define the account specific information
    # find the Access Key under preferences > User Advanced Options
    accessKey = 'vtigeraccesskeyhere'
    vtigerserver = 'https://someurl.od1.vtiger.com'
    url = '%s/webservice.php' % vtigerserver
    username = 'userloginname@email'
    # let's set up the session
    # get the token using 'getchallenge' operation
    values = {'operation': 'getchallenge', 'username': username}
    url = url + "?operation=" + \
          values['operation'] + "&username=" + values['username']
    response = requests.get(url)
    token = response.json()['result']['token']
    tempkey = (token + accessKey).encode('utf-8')
    key = md5(tempkey)
    tokenizedAccessKey = key.hexdigest()
    values['accessKey'] = tokenizedAccessKey
    payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; " \
              "name=\"operation\"\r\n\r\nlogin\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: " \
              "form-data; name=\"username\"\r\n\r\n" + \
              username + "\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; " \
                         "name=\"accessKey\"\r\n\r\n" + \
              tokenizedAccessKey + "\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--"
    headers = {
        'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        'Cache-Control': "no-cache"
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    # set the sessionName
    values['sessionName'] = response.json()['result']['sessionName']
    return values['sessionName']


ssessionName = getAuthVtiger()

wirte_contents = []
for i in range(1, 100000, 100):
    url = "https://someurl.od1.vtiger.com/webservice.php?operation=query&sessionName=" + ssessionName + "&query" \
                                                                                                        "=SELECT * " \
                                                                                                        "FROM " \
                                                                                                        "HelpDesk " \
                                                                                                        "LIMIT " + str(
        i) + "," + str(i + 99) + ";"

    response = requests.get(url)

    results = response.json()['result']

    wirte_contents = wirte_contents + results

    if len(results) < 100:
        break
# print(wirte_contents[0])
# print(len(wirte_contents))
es = Elasticsearch("192.168.0.114:9200")

for item in wirte_contents:
    try:
        item['weblink'] = "https://someurl.od1.vtiger.com/index.php?module=HelpDesk&view=Detail&record=" + \
                          (item['id'])[2:] + \
                          "&mode=showDetailViewByMode&requestMode=full&app=INVENTORY"
        payload = item

        result = es.index(index="tm_vtiger_helpdesk", doc_type="v_helpdesk",
                          id="vtiger_helpdesk" + payload['id'], body=payload)
    except TransportError:
        print(payload)
        pass
    # print(result)
