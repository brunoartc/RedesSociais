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

def scrape(trendurl):
    '''
    Insert the 25 Trending repos os the day to MySQL
    '''
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

def job():
    strdate = datetime.datetime.now().strftime('%Y-%m-%d')

    url = 'https://github.com/trending/'
    scrape(url)


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
    sqlconn = MySqlConn()
    repos = sqlconn.run('SELECT reponame FROM repo;')
    sqlconn.connection.close()
    for repo in repos:
        reponame = repo[0]
        # print(reponame)
        try:
            repolang = getLanguagesFromRepos({0: {'full_name': reponame}})[0]['topLang']
        except Exception as e:
            print(e)
            repolang = "B+NULL"
        # print(repolang)
        print(repolang)
        sqlconn = MySqlConn()
        repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
        try:
            # sqlconn.run('SELECT * FROM language WHERE name="%s";' %(repolang))
            langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(repolang))[0][0]
            sqlconn.run('INSERT INTO contains (repoid, langid) VALUES (%d, %d);' %(repoid, langid))
        except:
            sqlconn.run('INSERT INTO language (name) VALUES ("%s");' %(repolang))
            langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(repolang))[0][0]
            sqlconn.run('INSERT INTO contains (repoid, langid) VALUES (%d, %d);' %(repoid, langid))
        sqlconn.connection.commit()
        sqlconn.connection.close()


def devsLangsToMysql():
    sqlconn = MySqlConn()
    devs = sqlconn.run('SELECT username FROM dev;')
    sqlconn.connection.close()
    for dev in devs:
        username = dev[0]
        try:
            devlang = getRepos(username)['topLang']
            devlang = sorted(devlang.items(), key=lambda kv: kv[1])
            devlang = devlang[-1][0]
        except Exception as e:
            print(e)
            devlang = "B+NULL"
        print(devlang)
        sqlconn = MySqlConn()
        devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(username))[0][0]
        try:
            langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(devlang))[0][0]
            sqlconn.run('INSERT INTO uses (devid, langid) VALUES (%d, %d);' %(devid, langid))
        except:
            sqlconn.run('INSERT INTO language (name) VALUES ("%s");' %(devlang))
            langid = sqlconn.run('SELECT id FROM language WHERE name="%s";' %(devlang))[0][0]
            sqlconn.run('INSERT INTO uses (devid, langid) VALUES (%d, %d);' %(devid, langid))
        sqlconn.connection.commit()
        sqlconn.connection.close()

def repoLangToGml():
    tmp = 'graph [\n  directed 1\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM language;')
    langs_ids = []
    # Creating nodes for devs
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




if __name__ == '__main__':
    # job()
    # devsToMysql()
    # reposLangsToMysql()
    # repoLangToGml()
    devsLangsToMysql()