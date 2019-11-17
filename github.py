import requests
import time

def getRepos(username):
    resp = {}

    url = 'https://api.github.com/users/' + username + '/repos'


    headers = {'Authorization': 'token 96a382506c4e02c7a4eb90aeddc05b11dc419ec3'}
    r = requests.get(url, headers=headers).json()

    # username = 'chends888'
    # token = 'e4146d86fb322e59918b295b95ca6b1b61a2f031'

    # r = requests.get(url, auth=(username,token)).json()


    # r = requests.get(url).json()

    topLang = {}

    topLang_all = {}
    

    #print(r)

    for i in range(len(r)):
        #http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator} ???

        # urll = 'http://api.github.com/repos/' + r[i]['full_name'] + '/contributors?client_id=1c744c74d696e97f7efa&client_secret=b3ad57358f058d6c6dc12e49d4066500b8b0a1b5'


        url_l = 'http://api.github.com/repos/' + r[i]['full_name'] + '/languages'

        # rr = requests.get(urll)
        rr_l = requests.get(url_l, headers=headers)
        # time.sleep(1)
        if (rr_l.status_code == 200):
            # rr = rr.json()
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

            temp = {'full_name': r[i]['full_name'], 'language':r[i]['language'], 'contributors' :  [], 'langs' : topLang_exp}
            if r[i]['language'] in topLang.keys():
                topLang[r[i]['language']] += 1
            else:
                topLang[r[i]['language']] = 1
        else:
            print(rr_l.json())
        resp[i]=temp
    return ({'repos': resp, 'topLang': topLang, 'languages': topLang_all})


def getLanguagesFromRepos(repos, languages_search=[]):
    resp = []

    for i in repos:
        #print(repos[i])

        # url = 'https://api.github.com/search/code?q=repo:' + repos[i]['full_name'] + "&client_id=1c744c74d696e97f7efa&client_sercret=b3ad57358f058d6c6dc12e49d4066500b8b0a1b5"
        url = 'https://api.github.com/repos/' + repos[i]['full_name'] + "?client_id=1c744c74d696e97f7efa&client_sercret=b3ad57358f058d6c6dc12e49d4066500b8b0a1b5"
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
                url = 'https://api.github.com/search/code?q=language:'+ j + '+repo:'+repos[i]['full_name'] + "&client_id=1c744c74d696e97f7efa&client_sercret=b3ad57358f058d6c6dc12e49d4066500b8b0a1b5"

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
print(getRepos('chends888')['languages'])
# tmp = {0: {'full_name': 'chends888/AWSLambdaJobsHandler', 'language': 'Python', 'contributors': ['chends888']}}
#print(getLanguagesFromRepos(tmp))

