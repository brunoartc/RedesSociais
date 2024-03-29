# coding:utf-8


# Based on: https://github.com/bonfy/github-trending/blob/master/scraper.py
import datetime
import codecs
import requests
import os
import time
from pyquery import PyQuery as pq
import pymysql



class MySqlConn:
    def __init__(self):
        connection_options = {
            'host': 'localhost',
            'user': 'chends',
            'password': '8888',
            'database': 'gitdevsrepos'}
        self.connection = pymysql.connect(**connection_options)

    def run(self, query, args=None):
        with self.connection.cursor() as cursor:
            # print('Executing query: %s' %(cursor.mogrify(query, args)))
            cursor.execute(query, args)
            return cursor.fetchall()



def scrape(trendurl):

    HEADERS = {
        'User-Agent'		: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept'			: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding'	: 'gzip,deflate,sdch',
        'Accept-Language'	: 'zh-CN,zh;q=0.8'
    }

    r = requests.get(trendurl, headers=HEADERS)
    assert r.status_code == 200

    # print(r.encoding)

    d = pq(r.content)
    items = d('div.Box article.Box-row')

    for item in items:
        i = pq(item)
        name = i(".lh-condensed a").attr("href")
        url = "https://github.com" + name
        sqlconn = MySqlConn()
        if (trendurl == 'https://github.com/trending/developers/'):
            sqlconn.run('INSERT INTO dev (username) VALUES ("%s");' %(name[1:]))
        else:
            sqlconn.run('INSERT INTO repo (reponame, url) VALUES ("%s", "%s");' %(name[1:], url))
        sqlconn.connection.commit()
        sqlconn.connection.close()
    return 

def job():

    strdate = datetime.datetime.now().strftime('%Y-%m-%d')

    url = 'https://github.com/trending/developers/'
    scrape(url)


if __name__ == '__main__':
    job()