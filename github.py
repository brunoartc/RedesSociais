import requests


def getRepos(username):

    resp = {}

    url = 'https://api.github.com/users/'+username+'/repos?client_id=a4931b3b2248ac3013bc&client_secret=7a1798ed126acc6c16594304a46e0b1d8901d13f'

    r = requests.get(url).json()

    topLang = {}

    #print(r)

    for i in range(len(r)):

        #http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator} ???

        urll = 'http://api.github.com/repos/'+ r[i]['full_name'] + '/contributors?client_id=a4931b3b2248ac3013bc&client_secret=7a1798ed126acc6c16594304a46e0b1d8901d13f'
        
        rr = requests.get(urll)
        if (rr.status_code == 200):
            rr = rr.json()
            temp = {'full_name': r[i]['full_name'], 'language':r[i]['language'], 'contributors' :  [user['login'] for user in rr]}
            if r[i]['language'] in topLang.keys():
                topLang[r[i]['language']] += 1
            else:
                topLang[r[i]['language']] = 1

        resp[i]=temp
    return ({'repos': resp, 'topLang': topLang})


def getLanguagesFromRepos(repos, languages_search=[]):

    resp = []

    

    for i in repos:
        #print(repos[i])

        url = 'https://api.github.com/search/code?q=repo:'+repos[i]['full_name'] + "&client_id=a4931b3b2248ac3013bc&client_sercret=7a1798ed126acc6c16594304a46e0b1d8901d13f"
        url = 'https://api.github.com/repos/' +repos[i]['full_name'] + "?client_id=a4931b3b2248ac3013bc&client_sercret=7a1798ed126acc6c16594304a46e0b1d8901d13f"
        r = requests.get(url)
        print(r)
        if (r.status_code == 200):
            r = r.json()

            print(url, r)

            languages = {}
            for j in languages_search:
                # check languages proximity
                # url = 'https://api.github.com/search/code?q=language:'+(repos[i]['language'] if repos[i]['language']!=None else '') +'+repo:'+repos[i]['full_name']
                url = 'https://api.github.com/search/code?q=language:'+ j +'+repo:'+repos[i]['full_name'] + "&client_id=a4931b3b2248ac3013bc&client_sercret=7a1798ed126acc6c16594304a46e0b1d8901d13f"
                
                
                #print(url)
                r = requests.get(url).json()
                #print(r)
                if (r['total_count'] > 0):
                    languages[j] = {'total_count' : r['total_count'], 'items' : r['items'][0]['name']}
                else:
                    languages[j] = {'total_count' : r['total_count'], 'items' : None}
            resp.append( {'full_name':repos[i]['full_name'], 'languages':languages, 'topLang' : r['language'] } )

    return resp








print([[i['full_name'], i['topLang']] for i in getLanguagesFromRepos(getRepos('brunoartc')['repos'])])
#print(getRepos('brunoartc')['topLang'])

