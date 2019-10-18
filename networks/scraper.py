# coding:utf-8


# Based on: https://github.com/bonfy/github-trending/blob/master/scraper.py
import datetime
import codecs
import requests
import os
import time
from pyquery import PyQuery as pq




def scrape(filename, url):

    HEADERS = {
        'User-Agent'		: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept'			: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding'	: 'gzip,deflate,sdch',
        'Accept-Language'	: 'zh-CN,zh;q=0.8'
    }

    r = requests.get(url, headers=HEADERS)
    assert r.status_code == 200

    # print(r.encoding)

    d = pq(r.content)
    items = d('div.Box article.Box-row')

    tmp='['
    for item in items:
        i = pq(item)
        url = i(".lh-condensed a").attr("href")
        url = "https://github.com" + url
        tmp+='"'+u'{url}", '.format(url=url)
    tmp= tmp[:-2]
    tmp+=']'
    return tmp

def job():

    strdate = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = '{date}.json'.format(date=strdate)

    tmp='{\n'

    url = 'https://github.com/trending/'
    tmp += '  "repos":' + scrape(filename, url) + ',\n'

    url = 'https://github.com/trending/developers/'
    tmp += '  "devs":' + scrape(filename, url)

    tmp+='\n}'

    with open(filename, 'w') as f:
        f.write(tmp)


if __name__ == '__main__':
    job()