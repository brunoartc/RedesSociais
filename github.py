import requests


def getRepos(username):

    resp = {}

    url = 'https://api.github.com/users/'+username+'/repos?client_id=27b6c06c22f39c8b4762&client_secret=25eb0aaac1ca1e5a078a5eddd8971b8ed80627e5'

    r = requests.get(url).json()

    #print(r)

    for i in range(len(r)):

        #http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator} ???

        urll = 'http://api.github.com/repos/'+ r[i]['full_name'] + '/contributors?client_id=27b6c06c22f39c8b4762&client_secret=25eb0aaac1ca1e5a078a5eddd8971b8ed80627e5'
        #print(urll)
        rr = requests.get(urll).json()

        temp = {'full_name': r[i]['full_name'], 'language':r[i]['language'], 'contributors' :  [user['login'] for user in rr]}
        resp[i]=temp
    return resp


def getLanguagesFromRepos(repos, languages_search=None):

    resp = []

    for i in repos:
        #print(repos[i])
        languages = {}
        for j in languages_search:
            # check languages proximity
            # url = 'https://api.github.com/search/code?q=language:'+(repos[i]['language'] if repos[i]['language']!=None else '') +'+repo:'+repos[i]['full_name']
            url = 'https://api.github.com/search/code?q=language:'+ j +'+repo:'+repos[i]['full_name']
            #print(url)
            r = requests.get(url).json()
            if (r['total_count'] > 0):
                languages[j] = {'total_count' : r['total_count'], 'items' : r['items'][0]['name']}
            else:
                languages[j] = {'total_count' : r['total_count'], 'items' : None}
        resp.append( {'full_name':repos[i]['full_name'], 'languages':languages } )

    return resp








print(getLanguagesFromRepos(getRepos('brunoartc'), ["C", "Cpp"]))


