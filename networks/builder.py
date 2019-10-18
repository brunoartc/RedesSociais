import json
import sys
import requests

def getRepos(usr_url):

    api_url= usr_url[:8] + "api." + usr_url[8:]
    api_url= api_url[:22]+ "/users" + api_url[22:]
    api_url+= '/repos'

    resp = {}
    r = requests.get(api_url).json()

    for i in range(len(r)):
        temp = {'full_name': r[i]['full_name'], 'language':r[i]['language']}
        resp[i]=temp
    return resp


if len(sys.argv) != 2:
    print("Esperava como argumento o nome do arquivo")
filename= sys.argv[1]

with open(filename) as f:
    data= json.load(f)

r= getRepos(data["devs"][0])
print(r)