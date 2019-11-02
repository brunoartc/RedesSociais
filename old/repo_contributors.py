import requests


def getRepos(username):

    resp = {}

    url = 'https://api.github.com/users/'+username+'/repos'

    r = requests.get(url).json()

    print(url)

    for i in range(len(r)):
        temp = {'full_name': r[i]['full_name'], 'language':r[i]['language']}
        resp[i]=temp
    return resp


def getLanguagesFromRepos(repos, languages=None):

    resp = {}

    for i in repos:
        print(repos[i])
        languages = {}
        for j in range(languages):
            # check languages proximity
            # url = 'https://api.github.com/search/code?q=language:'+(repos[i]['language'] if repos[i]['language']!=None else '') +'+repo:'+repos[i]['full_name']
            url = 'https://api.github.com/search/code?q=language:'+ j +'+repo:'+repos[i]['full_name']
            r = requests.get(url).json()
            languages[j] = {'total_count' : r['total_count'], 'items' : r['items']}
        resp = {'full_name':repos[i]['full_name'], 'languages':languages} 


getLanguagesFromRepos(getRepos('brunoartc'))


