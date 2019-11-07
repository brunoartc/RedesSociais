import requests

def getRepos(username):
    resp = {}

    url = 'https://api.github.com/users/' + username + '/repos?client_id=36a1e33eece028435910&client_secret=c3a3ac09badfdb95b9679a70567a919b94501c1e'

    r = requests.get(url).json()

    topLang = {}

    topLang_all = {}
    

    #print(r)

    for i in range(len(r)):
        #http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator} ???

        urll = 'http://api.github.com/repos/' + r[i]['full_name'] + '/contributors?client_id=36a1e33eece028435910&client_secret=c3a3ac09badfdb95b9679a70567a919b94501c1e'


        url_l = 'http://api.github.com/repos/' + r[i]['full_name'] + '/languages?client_id=36a1e33eece028435910&client_secret=6f5cac313d3f620b5a2d569e8a82a5fb6d1ec876'

        rr = requests.get(urll)
        rr_l = requests.get(url_l)
        if (rr.status_code == 200):
            rr = rr.json()
            rr_l = rr_l.json()

            topLang_exp = {}

            for j in rr_l.keys():
                if i in topLang_exp.keys():
                    topLang_exp[j] += 1
                else:
                    topLang_exp[j] = 1

                if i in topLang_all.keys():
                    topLang_all[j] += rr_l[j]
                else:
                    topLang_all[j] = rr_l[j]

            temp = {'full_name': r[i]['full_name'], 'language':r[i]['language'], 'contributors' :  [user['login'] for user in rr], 'langs' : topLang_exp}
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

        # url = 'https://api.github.com/search/code?q=repo:' + repos[i]['full_name'] + "&client_id=36a1e33eece028435910&client_sercret=c3a3ac09badfdb95b9679a70567a919b94501c1e"
        url = 'https://api.github.com/repos/' + repos[i]['full_name'] + "?client_id=36a1e33eece028435910&client_sercret=c3a3ac09badfdb95b9679a70567a919b94501c1e"
        r = requests.get(url)
        url_languages = 'https://api.github.com/repos/' + repos[i]['full_name'] + '/languages'
        r_lang = requests.get(url_languages)
        # print(r.json())
        # print(r)
        if (r.status_code == 200):
            r = r.json()
            # print(r)

            # print(url, r)

	    

            languages = r_lang.json()
            for j in languages_search:
                # check languages proximity
                # url = 'https://api.github.com/search/code?q=language:'+(repos[i]['language'] if repos[i]['language']!=None else '') +'+repo:'+repos[i]['full_name']
                url = 'https://api.github.com/search/code?q=language:'+ j + '+repo:'+repos[i]['full_name'] + "&client_id=36a1e33eece028435910&client_sercret=c3a3ac09badfdb95b9679a70567a919b94501c1e"

                #print(url)
                r = requests.get(url).json()
                #print(r)
                if (r['total_count'] > 0):
                    languages[j] = {'total_count' : r['total_count'], 'items' : r['items'][0]['name']}
                else:
                    languages[j] = {'total_count' : r['total_count'], 'items' : None}
            resp.append( {'full_name':repos[i]['full_name'], 'languages':languages, 'topLang' : r['language'] } )

    return resp

# print([[i['full_name'], i['topLang']] for i in getLanguagesFromRepos(getRepos('brunoartc')['repos'])])
print(getRepos('chends888'))
tmp = {0: {'full_name': 'chends888/AWSLambdaJobsHandler', 'language': 'Python', 'contributors': ['chends888']}}
#print(getLanguagesFromRepos(tmp))

