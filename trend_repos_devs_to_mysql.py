# coding:utf-8

# Based on: https://github.com/bonfy/github-trending/blob/master/scraper.py
import datetime
import codecs
import requests
import os
import time
from pyquery import PyQuery as pq
import pymysql
from github import getLanguagesFromRepos, getRepos


class MySqlConn:
    def __init__(self):
        connection_options = {
            'host': 'localhost',
            'user': 'chends',
            'password': '8888',
            'database': 'gitrepodevlang'}
        self.connection = pymysql.connect(**connection_options)

    def run(self, query, args=None):
        with self.connection.cursor() as cursor:
            # print('Executing query: %s' %(cursor.mogrify(query, args)))
            cursor.execute(query, args)
            return cursor.fetchall()

def scrape():
    '''
    Insert the 25 Trending repos of the day to MySQL
    '''
    trendurl = 'https://github.com/trending?since=monthly'
    HEADERS = {
        'User-Agent'		: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept'			: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding'	: 'gzip,deflate,sdch',
        'Accept-Language'	: 'zh-CN,zh;q=0.8'
    }

    r = requests.get(trendurl, headers=HEADERS)
    assert r.status_code == 200

    d = pq(r.content)
    items = d('div.Box article.Box-row')

    for item in items:
        i = pq(item)
        name = i(".lh-condensed a").attr("href")
        url = "https://github.com" + name
        sqlconn = MySqlConn()
        sqlconn.run('INSERT INTO repo (reponame, url) VALUES ("%s", "%s");' %(name[1:], url))
        sqlconn.connection.commit()
        sqlconn.connection.close()

# def job():
#     # strdate = datetime.datetime.now().strftime('%Y-%m-%d')

#     # url = 'https://github.com/trending/'
#     url = 'https://github.com/trending?since=monthly'
#     scrape(url)


def devsToMysql():
    '''
    Insert contributors from the repos to MySQL
    '''
    sqlconn = MySqlConn()
    repos = sqlconn.run('SELECT reponame FROM repo;')
    sqlconn.connection.close()
    for repo in repos:
        reponame = repo[0]
        url = 'http://api.github.com/repos/'+ reponame + '/contributors?anon=1'
        r = requests.get(url).json()
        for i in range(len(r)):
            try:
                devname = r[i]['login']
            except:
                pass
            sqlconn = MySqlConn()
            repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
            try:
                devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(devname))[0][0]
            except:
                sqlconn.run('INSERT INTO dev (username) VALUES ("%s");' %(devname))
            sqlconn.connection.commit()
            sqlconn.connection.close()

def reposLangsToMysql():
    '''
    Insert repos languages and link them in MySQL
    '''
    sqlconn = MySqlConn()
    repos = sqlconn.run('SELECT reponame FROM repo;')
    sqlconn.connection.close()
    for repo in repos:
        reponame = repo[0]
        # print(reponame)
        try:
            repolangs = getLanguagesFromRepos({0: {'full_name': reponame}})[0]['languages']
            # print(repolangs)
        except Exception as e:
            print(e)
            repolangs = "B+NULL"
        # print(repolangs)
        print(repolangs)
        sqlconn = MySqlConn()
        repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
        sqlconn.connection.close()
        for lang in repolangs.keys():
            sqlconn = MySqlConn()
            print(lang)
            try:
                    langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(lang))[0][0]
                    sqlconn.run('INSERT INTO contains (repoid, langid) VALUES (%d, %d);' %(repoid, langid))
            except:
                    sqlconn.run('INSERT INTO language (name) VALUES ("%s");' %(lang))
                    langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(lang))[0][0]
                    sqlconn.run('INSERT INTO contains (repoid, langid) VALUES (%d, %d);' %(repoid, langid))
            sqlconn.connection.commit()
            sqlconn.connection.close()


def devsLangsToMysql():
    '''
    Insert and relation User-Language to MySQL
    '''
    sqlconn = MySqlConn()
    devs = sqlconn.run('SELECT username FROM dev;')
    sqlconn.connection.close()
    for dev in devs:
        username = dev[0]
        sqlconn = MySqlConn()
        devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(username))[0][0]
        sqlconn.connection.close()
        try:
            devlangs = getRepos(username)['languages']
            # devlangs = sorted(devlangs.items(), key=lambda kv: kv[1])
            # devlangs = devlangs[-1][0]
        except Exception as e:
            print(e)
            devlangs = {"B+NULL": None}
        print(devlangs)
        # sqlconn.connection.close()

        for lang in devlangs.keys():
            # print(devid, lang)
            sqlconn = MySqlConn()
            try:
                langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(lang))[0][0]
                print(devid, langid)
                sqlconn.run('INSERT INTO uses (devid, langid) VALUES (%d, %d);' %(devid, langid))
            except:
                sqlconn.run('INSERT INTO language (name) VALUES ("%s");' %(lang))
                langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(lang))[0][0]
                print(devid, langid)
                sqlconn.run('INSERT INTO uses (devid, langid) VALUES (%d, %d);' %(devid, langid))
            sqlconn.connection.commit()
            sqlconn.connection.close()

def repoLangToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM language;')
    langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(langname))[0][0]
        langs_ids.append([langid, langname])
        print(langname)
        tmp += '  node [\n    id "' + str(langname) + '"\n  ]\n'

    # Creating nodes for repos
    repos = sqlconn.run('SELECT reponame FROM repo;')
    repos_ids = []
    for reponame in repos:
        reponame = reponame[0]
        repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
        repos_ids.append([repoid, reponame])
        tmp += '  node [\n    id "' + str(reponame) + '"\n  ]\n'

    # Adding edges between languages and repos
    for repo in repos_ids:
        repolangs = sqlconn.run('SELECT langid FROM contains WHERE repoid=%d;' %(repo[0]))
        for langid in repolangs:
            langid = langid[0]
            langname = sqlconn.run('SELECT name FROM language WHERE id="%s";' %(langid))[0][0]
            tmp += '  edge [\n    source "' + repo[1] +'"\n    target "' + str(langname)+'"\n  ]\n'

    sqlconn.connection.close()

    tmp += ']'
    filename = 'data/repos_langs.gml'
    with open(filename, 'w') as f:
        f.write(tmp)


def devLangToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM language;')
    # langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(langname))[0][0]
        # langs_ids.append([langid, langname])
        print(langname)
        tmp += '  node [\n    id "/' + str(langname) + '"\n  ]\n'

    # Creating nodes for devs
    devs = sqlconn.run('SELECT username FROM dev;')
    devs_ids = []
    for dev in devs:
        username = dev[0]
        devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(username))[0][0]
        devs_ids.append([devid, username])
        tmp += '  node [\n    id "' + str(username) + '"\n  ]\n'

    # Adding edges between languages and devs
    for dev in devs_ids:
        devlangs = sqlconn.run('SELECT langid FROM uses WHERE devid=%d;' %(dev[0]))
        for langid in devlangs:
            langid = langid[0]
            langname = sqlconn.run('SELECT name FROM language WHERE id="%s";' %(langid))[0][0]
            tmp += '  edge [\n    source "' + dev[1] +'"\n    target "/' + str(langname)+'"\n  ]\n'

    sqlconn.connection.close()

    tmp += ']'
    filename = 'data/devs_langs.gml'
    with open(filename, 'w') as f:
        f.write(tmp)

def repoLangOneModeToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM language;')
    langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(langname))[0][0]
        langs_ids.append([langid, langname])
        tmp += '  node [\n    id "' + str(langname) + '"\n  ]\n'

    repolen = len(sqlconn.run('SELECT id FROM repo;'))
    meanrepos = repolen/len(sqlconn.run('SELECT langid, COUNT(langid) FROM contains GROUP BY langid;'))
    poplangs = sqlconn.run('SELECT langid, COUNT(langid) AS c FROM contains GROUP BY langid HAVING c>%d;' %(meanrepos))

    # Adding edges between languages and repos
    for lang1 in poplangs:
        lang1name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang1[0]))
        for lang2 in poplangs:
            lang2name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang2[0]))
            if (lang1name != lang2name):
                tmp += '  edge [\n    source "' + lang1name[0][0] +'"\n    target "' + lang2name[0][0] +'"\n  ]\n'

    sqlconn.connection.close()
    tmp += ']'
    filename = 'data/repos_langs_onemode.gml'
    with open(filename, 'w') as f:
        f.write(tmp)

def devLangOneModeToGml():
    tmp = 'graph [\n  directed 1\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM language;')
    langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(langname))[0][0]
        langs_ids.append([langid, langname])
        tmp += '  node [\n    id "' + str(langname) + '"\n  ]\n'

    devlen = len(sqlconn.run('SELECT id FROM dev;'))
    meandev = devlen/len(sqlconn.run('SELECT langid, COUNT(langid) FROM uses GROUP BY langid;'))
    poplangs = sqlconn.run('SELECT langid, COUNT(langid) AS c FROM uses GROUP BY langid HAVING c>%d;' %(meandev))

    # Adding edges between languages and repos
    for lang1 in poplangs:
        lang1name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang1[0]))
        for lang2 in poplangs:
            lang2name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang2[0]))
            if (lang1name != lang2name):
                tmp += '  edge [\n    source "' + lang1name[0][0] +'"\n    target "' + lang2name[0][0] +'"\n  ]\n'

    sqlconn.connection.close()
    tmp += ']'
    filename = 'data/devs_langs_onemode.gml'
    with open(filename, 'w') as f:
        f.write(tmp)


if __name__ == '__main__':
    # scrape()
    # devsToMysql()
    # reposLangsToMysql()
    # devsLangsToMysql()
    # repoLangToGml()
    devLangToGml()
    # repoLangOneModeToGml()
    # devLangOneModeToGml()