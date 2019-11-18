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

def scrape_devs():
    '''
    Insert the 25 Trending repos of the day to MySQL
    '''
    trendurl = 'https://github.com/trending/developers?since=monthly'
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
        devname = i(".lh-condensed a").attr("href")[1:]
        # print(name)
        sqlconn = MySqlConn()
        sqlconn.run('INSERT INTO dev (username) VALUES ("%s");' %(devname))
        sqlconn.connection.commit()
        sqlconn.connection.close()

def scrape_repos():
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


def reposLangsToMysql():
    '''
    Insert repos languages and the relation Repo-Language to MySQL
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
                    langid = sqlconn.run('SELECT id FROM repolanguage WHERE name="%s";' %(lang))[0][0]
                    sqlconn.run('INSERT INTO contains (repoid, langid) VALUES (%d, %d);' %(repoid, langid))
            except:
                    sqlconn.run('INSERT INTO repolanguage (name) VALUES ("%s");' %(lang))
                    langid = sqlconn.run('SELECT id FROM repolanguage WHERE name="%s";' %(lang))[0][0]
                    sqlconn.run('INSERT INTO contains (repoid, langid) VALUES (%d, %d);' %(repoid, langid))
            sqlconn.connection.commit()
            sqlconn.connection.close()


def devsLangsToMysql():
    '''
    Insert devs languages and the relation User-Language to MySQL
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
            # print(devlangs)
            # devlangs = sorted(devlangs.items(), key=lambda kv: kv[1])
            # devlangs = devlangs[-1][0]
        except Exception as e:
            print(e)
            devlangs = {"B+NULL": None}
        print(devlangs)

        for lang in devlangs.keys():
            # print(devid, lang)
            sqlconn = MySqlConn()
            try:
                langid = sqlconn.run('SELECT id FROM devlanguage WHERE name="%s";' %(lang))[0][0]
                print(devid, langid)
                sqlconn.run('INSERT INTO uses (devid, langid) VALUES (%d, %d);' %(devid, langid))
            except:
                sqlconn.run('INSERT INTO devlanguage (name) VALUES ("%s");' %(lang))
                langid = sqlconn.run('SELECT id FROM devlanguage WHERE name="%s";' %(lang))[0][0]
                print(devid, langid)
                sqlconn.run('INSERT INTO uses (devid, langid) VALUES (%d, %d);' %(devid, langid))
            sqlconn.connection.commit()
            sqlconn.connection.close()

def repoLangToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM repolanguage;')
    langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM repolanguage WHERE name="%s";' %(langname))[0][0]
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
            langname = sqlconn.run('SELECT name FROM repolanguage WHERE id="%s";' %(langid))[0][0]
            tmp += '  edge [\n    source "' + repo[1] +'"\n    target "' + str(langname)+'"\n  ]\n'

    sqlconn.connection.close()

    tmp += ']'
    filename = 'data/repos_langs.gml'
    with open(filename, 'w') as f:
        f.write(tmp)


def devLangToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM devlanguage;')
    # langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM devlanguage WHERE name="%s";' %(langname))[0][0]
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
            langname = sqlconn.run('SELECT name FROM devlanguage WHERE id="%s";' %(langid))[0][0]
            tmp += '  edge [\n    source "' + dev[1] +'"\n    target "/' + str(langname)+'"\n  ]\n'

    sqlconn.connection.close()

    tmp += ']'
    filename = 'data/devs_langs.gml'
    with open(filename, 'w') as f:
        f.write(tmp)

def repoLangOneModeToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM repolanguage;')
    langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM repolanguage WHERE name="%s";' %(langname))[0][0]
        langs_ids.append([langid, langname])
        tmp += '  node [\n    id "' + str(langname) + '"\n  ]\n'

    '''
    # Gathering the "repo share" data
    repos = sqlconn.run('SELECT reponame FROM repo;')
    popdict = {}
    lang_dict = {}
    for lang1 in langs_ids:
        print(lang1[0])
        # lang1name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang1[0]))
        for lang2 in langs_ids[langs_ids.index(lang1) + 1:]:
            if (lang1[0] != lang2[0]):
                reposshared = 0
                for reponame in repos:
                    reponame = reponame[0]
                    repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
                    langpop = sqlconn.run('SELECT COUNT(repoid) FROM contains WHERE repoid=%d AND (langid=%d OR langid=%d);' %(repoid, lang1[0], lang2[0]))[0][0]
                    if(langpop > 1):
                        reposshared += 1
                        lang_dict[lang1[1] + lang2[1]] = reposshared
                        #print(langpop)
                if reposshared in popdict.keys():
                    popdict[reposshared] += 1
                else:
                    popdict[reposshared] = 1
    print(popdict)
    print(lang_dict)

    '''

    sqlconn.connection.close()

    popdict = {3: 45, 2: 164, 1: 1249, 0: 1045, 7: 5, 5: 9, 11: 3, 6: 6, 4: 25, 9: 3, 13: 1, 10: 1}
    lang_dict = {'Jupyter NotebookPython': 3, 'Jupyter NotebookJavaScript': 2, 'Jupyter NotebookC++': 1, 'Jupyter NotebookShell': 3, 'Jupyter NotebookMATLAB': 1, 'Jupyter NotebookHTML': 2, 'Jupyter NotebookJava': 1, 'Jupyter NotebookCSS': 1, 'Jupyter NotebookDockerfile': 2, 'Jupyter NotebookMakefile': 1, 'Jupyter NotebookRuby': 1, 'Jupyter NotebookPHP': 1, 'Jupyter NotebookASP': 1, 'Jupyter NotebookXSLT': 1, 'PythonJavaScript': 7, 'PythonC++': 5, 'PythonShell': 11, 'PythonMATLAB': 2, 'PythonHTML': 7, 'PythonJava': 3, 'PythonCSS': 5, 'PythonDockerfile': 6, 'PythonTypeScript': 2, 'PythonInno Setup': 1, 'PythonBatchfile': 4, 'PythonPowerShell': 2, 'PythonGroovy': 1, 'PythonMakefile': 9, 'PythonRuby': 3, 'PythonObjective-C': 2, 'PythonObjective-C++': 2, 'PythonClojure': 1, 'PythonPerl 6': 1, 'PythonPHP': 3, 'PythonVisual Basic': 1, 'PythonPerl': 4, 'PythonC': 4, 'PythonGo': 3, 'PythonF#': 1, 'PythonCoffeeScript': 1, 'PythonRust': 2, 'PythonC#': 2, 'PythonR': 3, 'PythonRoff': 4, 'PythonShaderLab': 1, 'PythonSwift': 2, 'PythonLua': 1, 'PythonHLSL': 1, 'PythonHack': 1, 'PythonLLVM': 1, 'PythonAssembly': 1, 'PythonCMake': 1, 'PythonCuda': 1, 'PythonOCaml': 1, 'PythonAwk': 1, 'PythonM4': 1, 'PythonTeX': 1, 'PythonEmacs Lisp': 2, 'PythonSmalltalk': 1, 'PythonPawn': 1, 'PythonCool': 1, 'PythonVim script': 1, 'PythonFortran': 1, 'PythonMathematica': 1, 'PythonM': 1, 'PythonSuperCollider': 1, 'PythonCommon Lisp': 1, 'PythonAppleScript': 1, 'PythonMercury': 1, 'PythonPascal': 1, 'PythonForth': 1, 'PythonRenderScript': 1, 'PythonDTrace': 2, 'PythonLogos': 1, 'PythonSmarty': 1, 'PythonASP': 1, 'PythonXSLT': 1, 'PythonKotlin': 1, 'PythonProlog': 1, 'JavaScriptC++': 4, 'JavaScriptShell': 9, 'JavaScriptMATLAB': 2, 'JavaScriptHTML': 13, 'JavaScriptJava': 3, 'JavaScriptCSS': 11, 'JavaScriptDockerfile': 5, 'JavaScriptTypeScript': 4, 'JavaScriptInno Setup': 1, 'JavaScriptBatchfile': 5, 'JavaScriptPowerShell': 2, 'JavaScriptGroovy': 1, 'JavaScriptMakefile': 6, 'JavaScriptRuby': 2, 'JavaScriptObjective-C': 2, 'JavaScriptObjective-C++': 2, 'JavaScriptClojure': 1, 'JavaScriptPerl 6': 1, 'JavaScriptPHP': 3, 'JavaScriptVisual Basic': 1, 'JavaScriptPerl': 3, 'JavaScriptC': 3, 'JavaScriptGo': 3, 'JavaScriptF#': 1, 'JavaScriptCoffeeScript': 1, 'JavaScriptRust': 2, 'JavaScriptC#': 2, 'JavaScriptR': 3, 'JavaScriptRoff': 3, 'JavaScriptShaderLab': 1, 'JavaScriptSwift': 2, 'JavaScriptLua': 1, 'JavaScriptHLSL': 1, 'JavaScriptHack': 1, 'JavaScriptLLVM': 1, 'JavaScriptAssembly': 1, 'JavaScriptCMake': 1, 'JavaScriptCuda': 1, 'JavaScriptOCaml': 1, 'JavaScriptAwk': 1, 'JavaScriptM4': 1, 'JavaScriptTeX': 1, 'JavaScriptEmacs Lisp': 2, 'JavaScriptSmalltalk': 1, 'JavaScriptPawn': 1, 'JavaScriptCool': 1, 'JavaScriptVim script': 1, 'JavaScriptFortran': 1, 'JavaScriptMathematica': 1, 'JavaScriptM': 1, 'JavaScriptSuperCollider': 1, 'JavaScriptCommon Lisp': 1, 'JavaScriptAppleScript': 1, 'JavaScriptMercury': 1, 'JavaScriptPascal': 1, 'JavaScriptForth': 1, 'JavaScriptRenderScript': 1, 'JavaScriptDTrace': 2, 'JavaScriptLogos': 1, 'JavaScriptVue': 1, 'JavaScriptPLpgSQL': 1, 'JavaScriptTSQL': 1, 'JavaScriptASP': 1, 'JavaScriptXSLT': 1, 'C++Shell': 5, 'C++MATLAB': 2, 'C++HTML': 4, 'C++Java': 3, 'C++CSS': 3, 'C++Dockerfile': 3, 'C++TypeScript': 1, 'C++Inno Setup': 1, 'C++Batchfile': 3, 'C++PowerShell': 1, 'C++Groovy': 1, 'C++Makefile': 4, 'C++Ruby': 1, 'C++Objective-C': 2, 'C++Objective-C++': 2, 'C++Clojure': 1, 'C++Perl 6': 1, 'C++PHP': 2, 'C++Visual Basic': 1, 'C++Perl': 3, 'C++C': 4, 'C++Go': 2, 'C++F#': 1, 'C++CoffeeScript': 1, 'C++Rust': 2, 'C++C#': 2, 'C++R': 3, 'C++Roff': 3, 'C++ShaderLab': 1, 'C++Swift': 2, 'C++Lua': 1, 'C++HLSL': 1, 'C++Hack': 1, 'C++LLVM': 1, 'C++Assembly': 1, 'C++CMake': 1, 'C++Cuda': 1, 'C++OCaml': 1, 'C++Awk': 1, 'C++M4': 1, 'C++TeX': 1, 'C++Emacs Lisp': 2, 'C++Smalltalk': 1, 'C++Pawn': 1, 'C++Cool': 1, 'C++Vim script': 1, 'C++Fortran': 1, 'C++Mathematica': 1, 'C++M': 1, 'C++SuperCollider': 1, 'C++Common Lisp': 1, 'C++AppleScript': 1, 'C++Mercury': 1, 'C++Pascal': 1, 'C++Forth': 1, 'C++RenderScript': 1, 'C++DTrace': 2, 'C++Logos': 1, 'C++Kotlin': 1, 'C++Prolog': 1, 'ShellMATLAB': 2, 'ShellHTML': 9, 'ShellJava': 4, 'ShellCSS': 7, 'ShellDockerfile': 7, 'ShellTypeScript': 3, 'ShellInno Setup': 1, 'ShellBatchfile': 5, 'ShellPowerShell': 2, 'ShellGroovy': 1, 'ShellMakefile': 10, 'ShellRuby': 3, 'ShellObjective-C': 2, 'ShellObjective-C++': 2, 'ShellClojure': 1, 'ShellPerl 6': 1, 'ShellPHP': 3, 'ShellVisual Basic': 1, 'ShellPerl': 4, 'ShellC': 4, 'ShellGo': 4, 'ShellF#': 1, 'ShellCoffeeScript': 1, 'ShellRust': 2, 'ShellC#': 2, 'ShellR': 3, 'ShellRoff': 4, 'ShellShaderLab': 1, 'ShellSwift': 2, 'ShellLua': 1, 'ShellHLSL': 1, 'ShellHack': 1, 'ShellLLVM': 1, 'ShellAssembly': 1, 'ShellCMake': 1, 'ShellCuda': 1, 'ShellOCaml': 1, 'ShellAwk': 1, 'ShellM4': 1, 'ShellTeX': 1, 'ShellEmacs Lisp': 2, 'ShellSmalltalk': 1, 'ShellPawn': 1, 'ShellCool': 1, 'ShellVim script': 1, 'ShellFortran': 1, 'ShellMathematica': 1, 'ShellM': 1, 'ShellSuperCollider': 1, 'ShellCommon Lisp': 1, 'ShellAppleScript': 1, 'ShellMercury': 1, 'ShellPascal': 1, 'ShellForth': 1, 'ShellRenderScript': 1, 'ShellDTrace': 2, 'ShellLogos': 1, 'ShellSmarty': 1, 'ShellASP': 1, 'ShellXSLT': 1, 'ShellKotlin': 1, 'ShellProlog': 1, 'MATLABHTML': 2, 'MATLABJava': 1, 'MATLABCSS': 2, 'MATLABDockerfile': 2, 'MATLABBatchfile': 1, 'MATLABMakefile': 1, 'MATLABObjective-C': 1, 'MATLABObjective-C++': 1, 'MATLABPHP': 1, 'MATLABPerl': 1, 'MATLABC': 1, 'MATLABGo': 1, 'MATLABRust': 1, 'MATLABC#': 1, 'MATLABR': 1, 'MATLABRoff': 1, 'MATLABSwift': 1, 'MATLABLLVM': 1, 'MATLABAssembly': 1, 'MATLABCMake': 1, 'MATLABCuda': 1, 'MATLABOCaml': 1, 'MATLABAwk': 1, 'MATLABM4': 1, 'MATLABTeX': 1, 'MATLABEmacs Lisp': 1, 'MATLABSmalltalk': 1, 'MATLABPawn': 1, 'MATLABCool': 1, 'MATLABVim script': 1, 'MATLABFortran': 1, 'MATLABMathematica': 1, 'MATLABM': 1, 'MATLABSuperCollider': 1, 'MATLABCommon Lisp': 1, 'MATLABAppleScript': 1, 'MATLABMercury': 1, 'MATLABPascal': 1, 'MATLABForth': 1, 'MATLABRenderScript': 1, 'MATLABDTrace': 1, 'MATLABLogos': 1, 'HTMLJava': 3, 'HTMLCSS': 11, 'HTMLDockerfile': 6, 'HTMLTypeScript': 4, 'HTMLInno Setup': 1, 'HTMLBatchfile': 6, 'HTMLPowerShell': 2, 'HTMLGroovy': 1, 'HTMLMakefile': 7, 'HTMLRuby': 2, 'HTMLObjective-C': 2, 'HTMLObjective-C++': 2, 'HTMLClojure': 1, 'HTMLPerl 6': 1, 'HTMLPHP': 3, 'HTMLVisual Basic': 1, 'HTMLPerl': 3, 'HTMLC': 4, 'HTMLGo': 3, 'HTMLF#': 1, 'HTMLCoffeeScript': 1, 'HTMLRust': 2, 'HTMLC#': 2, 'HTMLR': 3, 'HTMLRoff': 3, 'HTMLShaderLab': 1, 'HTMLSwift': 2, 'HTMLLua': 1, 'HTMLHLSL': 1, 'HTMLHack': 1, 'HTMLLLVM': 1, 'HTMLAssembly': 2, 'HTMLCMake': 1, 'HTMLCuda': 1, 'HTMLOCaml': 1, 'HTMLAwk': 1, 'HTMLM4': 1, 'HTMLTeX': 1, 'HTMLEmacs Lisp': 2, 'HTMLSmalltalk': 1, 'HTMLPawn': 1, 'HTMLCool': 1, 'HTMLVim script': 1, 'HTMLFortran': 1, 'HTMLMathematica': 1, 'HTMLM': 1, 'HTMLSuperCollider': 1, 'HTMLCommon Lisp': 1, 'HTMLAppleScript': 1, 'HTMLMercury': 1, 'HTMLPascal': 1, 'HTMLForth': 1, 'HTMLRenderScript': 1, 'HTMLDTrace': 2, 'HTMLLogos': 1, 'HTMLV': 1, 'HTMLVue': 1, 'HTMLPLpgSQL': 1, 'HTMLTSQL': 1, 'HTMLASP': 1, 'HTMLXSLT': 1, 'JavaCSS': 4, 'JavaDockerfile': 2, 'JavaTypeScript': 1, 'JavaInno Setup': 1, 'JavaBatchfile': 1, 'JavaPowerShell': 1, 'JavaGroovy': 1, 'JavaMakefile': 2, 'JavaRuby': 1, 'JavaObjective-C': 1, 'JavaObjective-C++': 1, 'JavaClojure': 1, 'JavaPerl 6': 1, 'JavaPHP': 1, 'JavaVisual Basic': 1, 'JavaPerl': 1, 'JavaC': 2, 'JavaGo': 1, 'JavaF#': 1, 'JavaCoffeeScript': 1, 'JavaRust': 1, 'JavaC#': 1, 'JavaR': 1, 'JavaRoff': 1, 'JavaShaderLab': 1, 'JavaSwift': 1, 'JavaLua': 1, 'JavaHLSL': 1, 'JavaHack': 1, 'JavaVue': 1, 'JavaPLpgSQL': 1, 'JavaTSQL': 1, 'JavaKotlin': 2, 'JavaProlog': 1, 'JavaFreeMarker': 1, 'CSSDockerfile': 5, 'CSSTypeScript': 4, 'CSSInno Setup': 1, 'CSSBatchfile': 4, 'CSSPowerShell': 2, 'CSSGroovy': 1, 'CSSMakefile': 5, 'CSSRuby': 1, 'CSSObjective-C': 2, 'CSSObjective-C++': 2, 'CSSClojure': 1, 'CSSPerl 6': 1, 'CSSPHP': 2, 'CSSVisual Basic': 1, 'CSSPerl': 2, 'CSSC': 2, 'CSSGo': 3, 'CSSF#': 1, 'CSSCoffeeScript': 1, 'CSSRust': 2, 'CSSC#': 2, 'CSSR': 2, 'CSSRoff': 2, 'CSSShaderLab': 1, 'CSSSwift': 2, 'CSSLua': 1, 'CSSHLSL': 1, 'CSSHack': 1, 'CSSLLVM': 1, 'CSSAssembly': 1, 'CSSCMake': 1, 'CSSCuda': 1, 'CSSOCaml': 1, 'CSSAwk': 1, 'CSSM4': 1, 'CSSTeX': 1, 'CSSEmacs Lisp': 1, 'CSSSmalltalk': 1, 'CSSPawn': 1, 'CSSCool': 1, 'CSSVim script': 1, 'CSSFortran': 1, 'CSSMathematica': 1, 'CSSM': 1, 'CSSSuperCollider': 1, 'CSSCommon Lisp': 1, 'CSSAppleScript': 1, 'CSSMercury': 1, 'CSSPascal': 1, 'CSSForth': 1, 'CSSRenderScript': 1, 'CSSDTrace': 1, 'CSSLogos': 1, 'CSSVue': 1, 'CSSPLpgSQL': 1, 'CSSTSQL': 1, 'CSSKotlin': 1, 'CSSFreeMarker': 1, 'DockerfileTypeScript': 3, 'DockerfileInno Setup': 1, 'DockerfileBatchfile': 4, 'DockerfilePowerShell': 1, 'DockerfileGroovy': 1, 'DockerfileMakefile': 6, 'DockerfileRuby': 1, 'DockerfileObjective-C': 2, 'DockerfileObjective-C++': 2, 'DockerfileClojure': 1, 'DockerfilePerl 6': 1, 'DockerfilePHP': 2, 'DockerfileVisual Basic': 1, 'DockerfilePerl': 2, 'DockerfileC': 3, 'DockerfileGo': 3, 'DockerfileF#': 1, 'DockerfileCoffeeScript': 1, 'DockerfileRust': 2, 'DockerfileC#': 2, 'DockerfileR': 2, 'DockerfileRoff': 2, 'DockerfileShaderLab': 1, 'DockerfileSwift': 2, 'DockerfileLua': 1, 'DockerfileHLSL': 1, 'DockerfileHack': 1, 'DockerfileLLVM': 1, 'DockerfileAssembly': 2, 'DockerfileCMake': 1, 'DockerfileCuda': 1, 'DockerfileOCaml': 1, 'DockerfileAwk': 1, 'DockerfileM4': 1, 'DockerfileTeX': 1, 'DockerfileEmacs Lisp': 1, 'DockerfileSmalltalk': 1, 'DockerfilePawn': 1, 'DockerfileCool': 1, 'DockerfileVim script': 1, 'DockerfileFortran': 1, 'DockerfileMathematica': 1, 'DockerfileM': 1, 'DockerfileSuperCollider': 1, 'DockerfileCommon Lisp': 1, 'DockerfileAppleScript': 1, 'DockerfileMercury': 1, 'DockerfilePascal': 1, 'DockerfileForth': 1, 'DockerfileRenderScript': 1, 'DockerfileDTrace': 1, 'DockerfileLogos': 1, 'DockerfileSmarty': 1, 'DockerfileV': 1, 'TypeScriptInno Setup': 1, 'TypeScriptBatchfile': 2, 'TypeScriptPowerShell': 1, 'TypeScriptGroovy': 1, 'TypeScriptMakefile': 2, 'TypeScriptRuby': 1, 'TypeScriptObjective-C': 1, 'TypeScriptObjective-C++': 1, 'TypeScriptClojure': 1, 'TypeScriptPerl 6': 1, 'TypeScriptPHP': 1, 'TypeScriptVisual Basic': 1, 'TypeScriptPerl': 1, 'TypeScriptC': 1, 'TypeScriptGo': 1, 'TypeScriptF#': 1, 'TypeScriptCoffeeScript': 1, 'TypeScriptRust': 1, 'TypeScriptC#': 1, 'TypeScriptR': 1, 'TypeScriptRoff': 1, 'TypeScriptShaderLab': 1, 'TypeScriptSwift': 1, 'TypeScriptLua': 1, 'TypeScriptHLSL': 1, 'TypeScriptHack': 1, 'Inno SetupBatchfile': 1, 'Inno SetupPowerShell': 1, 'Inno SetupGroovy': 1, 'Inno SetupMakefile': 1, 'Inno SetupRuby': 1, 'Inno SetupObjective-C': 1, 'Inno SetupObjective-C++': 1, 'Inno SetupClojure': 1, 'Inno SetupPerl 6': 1, 'Inno SetupPHP': 1, 'Inno SetupVisual Basic': 1, 'Inno SetupPerl': 1, 'Inno SetupC': 1, 'Inno SetupGo': 1, 'Inno SetupF#': 1, 'Inno SetupCoffeeScript': 1, 'Inno SetupRust': 1, 'Inno SetupC#': 1, 'Inno SetupR': 1, 'Inno SetupRoff': 1, 'Inno SetupShaderLab': 1, 'Inno SetupSwift': 1, 'Inno SetupLua': 1, 'Inno SetupHLSL': 1, 'Inno SetupHack': 1, 'BatchfilePowerShell': 1, 'BatchfileGroovy': 1, 'BatchfileMakefile': 6, 'BatchfileRuby': 1, 'BatchfileObjective-C': 2, 'BatchfileObjective-C++': 2, 'BatchfileClojure': 1, 'BatchfilePerl 6': 1, 'BatchfilePHP': 2, 'BatchfileVisual Basic': 1, 'BatchfilePerl': 3, 'BatchfileC': 4, 'BatchfileGo': 3, 'BatchfileF#': 1, 'BatchfileCoffeeScript': 1, 'BatchfileRust': 2, 'BatchfileC#': 2, 'BatchfileR': 3, 'BatchfileRoff': 3, 'BatchfileShaderLab': 1, 'BatchfileSwift': 2, 'BatchfileLua': 1, 'BatchfileHLSL': 1, 'BatchfileHack': 1, 'BatchfileLLVM': 1, 'BatchfileAssembly': 2, 'BatchfileCMake': 1, 'BatchfileCuda': 1, 'BatchfileOCaml': 1, 'BatchfileAwk': 1, 'BatchfileM4': 1, 'BatchfileTeX': 1, 'BatchfileEmacs Lisp': 2, 'BatchfileSmalltalk': 1, 'BatchfilePawn': 1, 'BatchfileCool': 1, 'BatchfileVim script': 1, 'BatchfileFortran': 1, 'BatchfileMathematica': 1, 'BatchfileM': 1, 'BatchfileSuperCollider': 1, 'BatchfileCommon Lisp': 1, 'BatchfileAppleScript': 1, 'BatchfileMercury': 1, 'BatchfilePascal': 1, 'BatchfileForth': 1, 'BatchfileRenderScript': 1, 'BatchfileDTrace': 2, 'BatchfileLogos': 1, 'BatchfileV': 1, 'PowerShellGroovy': 1, 'PowerShellMakefile': 2, 'PowerShellRuby': 1, 'PowerShellObjective-C': 1, 'PowerShellObjective-C++': 1, 'PowerShellClojure': 1, 'PowerShellPerl 6': 1, 'PowerShellPHP': 1, 'PowerShellVisual Basic': 1, 'PowerShellPerl': 1, 'PowerShellC': 1, 'PowerShellGo': 1, 'PowerShellF#': 1, 'PowerShellCoffeeScript': 1, 'PowerShellRust': 1, 'PowerShellC#': 1, 'PowerShellR': 1, 'PowerShellRoff': 1, 'PowerShellShaderLab': 1, 'PowerShellSwift': 1, 'PowerShellLua': 1, 'PowerShellHLSL': 1, 'PowerShellHack': 1, 'GroovyMakefile': 1, 'GroovyRuby': 1, 'GroovyObjective-C': 1, 'GroovyObjective-C++': 1, 'GroovyClojure': 1, 'GroovyPerl 6': 1, 'GroovyPHP': 1, 'GroovyVisual Basic': 1, 'GroovyPerl': 1, 'GroovyC': 1, 'GroovyGo': 1, 'GroovyF#': 1, 'GroovyCoffeeScript': 1, 'GroovyRust': 1, 'GroovyC#': 1, 'GroovyR': 1, 'GroovyRoff': 1, 'GroovyShaderLab': 1, 'GroovySwift': 1, 'GroovyLua': 1, 'GroovyHLSL': 1, 'GroovyHack': 1, 'MakefileRuby': 2, 'MakefileObjective-C': 2, 'MakefileObjective-C++': 2, 'MakefileClojure': 1, 'MakefilePerl 6': 1, 'MakefilePHP': 2, 'MakefileVisual Basic': 1, 'MakefilePerl': 4, 'MakefileC': 5, 'MakefileGo': 4, 'MakefileF#': 1, 'MakefileCoffeeScript': 1, 'MakefileRust': 2, 'MakefileC#': 2, 'MakefileR': 3, 'MakefileRoff': 4, 'MakefileShaderLab': 1, 'MakefileSwift': 2, 'MakefileLua': 1, 'MakefileHLSL': 1, 'MakefileHack': 1, 'MakefileLLVM': 1, 'MakefileAssembly': 2, 'MakefileCMake': 1, 'MakefileCuda': 1, 'MakefileOCaml': 1, 'MakefileAwk': 1, 'MakefileM4': 1, 'MakefileTeX': 1, 'MakefileEmacs Lisp': 2, 'MakefileSmalltalk': 1, 'MakefilePawn': 1, 'MakefileCool': 1, 'MakefileVim script': 1, 'MakefileFortran': 1, 'MakefileMathematica': 1, 'MakefileM': 1, 'MakefileSuperCollider': 1, 'MakefileCommon Lisp': 1, 'MakefileAppleScript': 1, 'MakefileMercury': 1, 'MakefilePascal': 1, 'MakefileForth': 1, 'MakefileRenderScript': 1, 'MakefileDTrace': 2, 'MakefileLogos': 1, 'MakefileSmarty': 1, 'MakefileV': 1, 'MakefileKotlin': 1, 'MakefileProlog': 1, 'RubyObjective-C': 1, 'RubyObjective-C++': 1, 'RubyClojure': 1, 'RubyPerl 6': 1, 'RubyPHP': 2, 'RubyVisual Basic': 1, 'RubyPerl': 2, 'RubyC': 1, 'RubyGo': 1, 'RubyF#': 1, 'RubyCoffeeScript': 1, 'RubyRust': 1, 'RubyC#': 1, 'RubyR': 1, 'RubyRoff': 2, 'RubyShaderLab': 1, 'RubySwift': 1, 'RubyLua': 1, 'RubyHLSL': 1, 'RubyHack': 1, 'RubyASP': 1, 'RubyXSLT': 1, 'Objective-CObjective-C++': 2, 'Objective-CClojure': 1, 'Objective-CPerl 6': 1, 'Objective-CPHP': 2, 'Objective-CVisual Basic': 1, 'Objective-CPerl': 2, 'Objective-CC': 2, 'Objective-CGo': 2, 'Objective-CF#': 1, 'Objective-CCoffeeScript': 1, 'Objective-CRust': 2, 'Objective-CC#': 2, 'Objective-CR': 2, 'Objective-CRoff': 2, 'Objective-CShaderLab': 1, 'Objective-CSwift': 2, 'Objective-CLua': 1, 'Objective-CHLSL': 1, 'Objective-CHack': 1, 'Objective-CLLVM': 1, 'Objective-CAssembly': 1, 'Objective-CCMake': 1, 'Objective-CCuda': 1, 'Objective-COCaml': 1, 'Objective-CAwk': 1, 'Objective-CM4': 1, 'Objective-CTeX': 1, 'Objective-CEmacs Lisp': 1, 'Objective-CSmalltalk': 1, 'Objective-CPawn': 1, 'Objective-CCool': 1, 'Objective-CVim script': 1, 'Objective-CFortran': 1, 'Objective-CMathematica': 1, 'Objective-CM': 1, 'Objective-CSuperCollider': 1, 'Objective-CCommon Lisp': 1, 'Objective-CAppleScript': 1, 'Objective-CMercury': 1, 'Objective-CPascal': 1, 'Objective-CForth': 1, 'Objective-CRenderScript': 1, 'Objective-CDTrace': 1, 'Objective-CLogos': 1, 'Objective-C++Clojure': 1, 'Objective-C++Perl 6': 1, 'Objective-C++PHP': 2, 'Objective-C++Visual Basic': 1, 'Objective-C++Perl': 2, 'Objective-C++C': 2, 'Objective-C++Go': 2, 'Objective-C++F#': 1, 'Objective-C++CoffeeScript': 1, 'Objective-C++Rust': 2, 'Objective-C++C#': 2, 'Objective-C++R': 2, 'Objective-C++Roff': 2, 'Objective-C++ShaderLab': 1, 'Objective-C++Swift': 2, 'Objective-C++Lua': 1, 'Objective-C++HLSL': 1, 'Objective-C++Hack': 1, 'Objective-C++LLVM': 1, 'Objective-C++Assembly': 1, 'Objective-C++CMake': 1, 'Objective-C++Cuda': 1, 'Objective-C++OCaml': 1, 'Objective-C++Awk': 1, 'Objective-C++M4': 1, 'Objective-C++TeX': 1, 'Objective-C++Emacs Lisp': 1, 'Objective-C++Smalltalk': 1, 'Objective-C++Pawn': 1, 'Objective-C++Cool': 1, 'Objective-C++Vim script': 1, 'Objective-C++Fortran': 1, 'Objective-C++Mathematica': 1, 'Objective-C++M': 1, 'Objective-C++SuperCollider': 1, 'Objective-C++Common Lisp': 1, 'Objective-C++AppleScript': 1, 'Objective-C++Mercury': 1, 'Objective-C++Pascal': 1, 'Objective-C++Forth': 1, 'Objective-C++RenderScript': 1, 'Objective-C++DTrace': 1, 'Objective-C++Logos': 1, 'ClojurePerl 6': 1, 'ClojurePHP': 1, 'ClojureVisual Basic': 1, 'ClojurePerl': 1, 'ClojureC': 1, 'ClojureGo': 1, 'ClojureF#': 1, 'ClojureCoffeeScript': 1, 'ClojureRust': 1, 'ClojureC#': 1, 'ClojureR': 1, 'ClojureRoff': 1, 'ClojureShaderLab': 1, 'ClojureSwift': 1, 'ClojureLua': 1, 'ClojureHLSL': 1, 'ClojureHack': 1, 'Perl 6PHP': 1, 'Perl 6Visual Basic': 1, 'Perl 6Perl': 1, 'Perl 6C': 1, 'Perl 6Go': 1, 'Perl 6F#': 1, 'Perl 6CoffeeScript': 1, 'Perl 6Rust': 1, 'Perl 6C#': 1, 'Perl 6R': 1, 'Perl 6Roff': 1, 'Perl 6ShaderLab': 1, 'Perl 6Swift': 1, 'Perl 6Lua': 1, 'Perl 6HLSL': 1, 'Perl 6Hack': 1, 'PHPVisual Basic': 1, 'PHPPerl': 2, 'PHPC': 2, 'PHPGo': 2, 'PHPF#': 1, 'PHPCoffeeScript': 1, 'PHPRust': 2, 'PHPC#': 2, 'PHPR': 2, 'PHPRoff': 2, 'PHPShaderLab': 1, 'PHPSwift': 2, 'PHPLua': 1, 'PHPHLSL': 1, 'PHPHack': 1, 'PHPLLVM': 1, 'PHPAssembly': 1, 'PHPCMake': 1, 'PHPCuda': 1, 'PHPOCaml': 1, 'PHPAwk': 1, 'PHPM4': 1, 'PHPTeX': 1, 'PHPEmacs Lisp': 1, 'PHPSmalltalk': 1, 'PHPPawn': 1, 'PHPCool': 1, 'PHPVim script': 1, 'PHPFortran': 1, 'PHPMathematica': 1, 'PHPM': 1, 'PHPSuperCollider': 1, 'PHPCommon Lisp': 1, 'PHPAppleScript': 1, 'PHPMercury': 1, 'PHPPascal': 1, 'PHPForth': 1, 'PHPRenderScript': 1, 'PHPDTrace': 1, 'PHPLogos': 1, 'PHPASP': 1, 'PHPXSLT': 1, 'Visual BasicPerl': 1, 'Visual BasicC': 1, 'Visual BasicGo': 1, 'Visual BasicF#': 1, 'Visual BasicCoffeeScript': 1, 'Visual BasicRust': 1, 'Visual BasicC#': 1, 'Visual BasicR': 1, 'Visual BasicRoff': 1, 'Visual BasicShaderLab': 1, 'Visual BasicSwift': 1, 'Visual BasicLua': 1, 'Visual BasicHLSL': 1, 'Visual BasicHack': 1, 'PerlC': 3, 'PerlGo': 2, 'PerlF#': 1, 'PerlCoffeeScript': 1, 'PerlRust': 2, 'PerlC#': 2, 'PerlR': 3, 'PerlRoff': 4, 'PerlShaderLab': 1, 'PerlSwift': 2, 'PerlLua': 1, 'PerlHLSL': 1, 'PerlHack': 1, 'PerlLLVM': 1, 'PerlAssembly': 1, 'PerlCMake': 1, 'PerlCuda': 1, 'PerlOCaml': 1, 'PerlAwk': 1, 'PerlM4': 1, 'PerlTeX': 1, 'PerlEmacs Lisp': 2, 'PerlSmalltalk': 1, 'PerlPawn': 1, 'PerlCool': 1, 'PerlVim script': 1, 'PerlFortran': 1, 'PerlMathematica': 1, 'PerlM': 1, 'PerlSuperCollider': 1, 'PerlCommon Lisp': 1, 'PerlAppleScript': 1, 'PerlMercury': 1, 'PerlPascal': 1, 'PerlForth': 1, 'PerlRenderScript': 1, 'PerlDTrace': 2, 'PerlLogos': 1, 'CGo': 2, 'CF#': 1, 'CCoffeeScript': 1, 'CRust': 2, 'CC#': 2, 'CR': 3, 'CRoff': 3, 'CShaderLab': 1, 'CSwift': 2, 'CLua': 1, 'CHLSL': 1, 'CHack': 1, 'CLLVM': 1, 'CAssembly': 2, 'CCMake': 1, 'CCuda': 1, 'COCaml': 1, 'CAwk': 1, 'CM4': 1, 'CTeX': 1, 'CEmacs Lisp': 2, 'CSmalltalk': 1, 'CPawn': 1, 'CCool': 1, 'CVim script': 1, 'CFortran': 1, 'CMathematica': 1, 'CM': 1, 'CSuperCollider': 1, 'CCommon Lisp': 1, 'CAppleScript': 1, 'CMercury': 1, 'CPascal': 1, 'CForth': 1, 'CRenderScript': 1, 'CDTrace': 2, 'CLogos': 1, 'CV': 1, 'CKotlin': 1, 'CProlog': 1, 'GoF#': 1, 'GoCoffeeScript': 1, 'GoRust': 2, 'GoC#': 2, 'GoR': 2, 'GoRoff': 2, 'GoShaderLab': 1, 'GoSwift': 2, 'GoLua': 1, 'GoHLSL': 1, 'GoHack': 1, 'GoLLVM': 1, 'GoAssembly': 1, 'GoCMake': 1, 'GoCuda': 1, 'GoOCaml': 1, 'GoAwk': 1, 'GoM4': 1, 'GoTeX': 1, 'GoEmacs Lisp': 1, 'GoSmalltalk': 1, 'GoPawn': 1, 'GoCool': 1, 'GoVim script': 1, 'GoFortran': 1, 'GoMathematica': 1, 'GoM': 1, 'GoSuperCollider': 1, 'GoCommon Lisp': 1, 'GoAppleScript': 1, 'GoMercury': 1, 'GoPascal': 1, 'GoForth': 1, 'GoRenderScript': 1, 'GoDTrace': 1, 'GoLogos': 1, 'GoSmarty': 1, 'F#CoffeeScript': 1, 'F#Rust': 1, 'F#C#': 1, 'F#R': 1, 'F#Roff': 1, 'F#ShaderLab': 1, 'F#Swift': 1, 'F#Lua': 1, 'F#HLSL': 1, 'F#Hack': 1, 'CoffeeScriptRust': 1, 'CoffeeScriptC#': 1, 'CoffeeScriptR': 1, 'CoffeeScriptRoff': 1, 'CoffeeScriptShaderLab': 1, 'CoffeeScriptSwift': 1, 'CoffeeScriptLua': 1, 'CoffeeScriptHLSL': 1, 'CoffeeScriptHack': 1, 'RustC#': 2, 'RustR': 2, 'RustRoff': 2, 'RustShaderLab': 1, 'RustSwift': 2, 'RustLua': 1, 'RustHLSL': 1, 'RustHack': 1, 'RustLLVM': 1, 'RustAssembly': 1, 'RustCMake': 1, 'RustCuda': 1, 'RustOCaml': 1, 'RustAwk': 1, 'RustM4': 1, 'RustTeX': 1, 'RustEmacs Lisp': 1, 'RustSmalltalk': 1, 'RustPawn': 1, 'RustCool': 1, 'RustVim script': 1, 'RustFortran': 1, 'RustMathematica': 1, 'RustM': 1, 'RustSuperCollider': 1, 'RustCommon Lisp': 1, 'RustAppleScript': 1, 'RustMercury': 1, 'RustPascal': 1, 'RustForth': 1, 'RustRenderScript': 1, 'RustDTrace': 1, 'RustLogos': 1, 'C#R': 2, 'C#Roff': 2, 'C#ShaderLab': 1, 'C#Swift': 2, 'C#Lua': 1, 'C#HLSL': 1, 'C#Hack': 1, 'C#LLVM': 1, 'C#Assembly': 1, 'C#CMake': 1, 'C#Cuda': 1, 'C#OCaml': 1, 'C#Awk': 1, 'C#M4': 1, 'C#TeX': 1, 'C#Emacs Lisp': 1, 'C#Smalltalk': 1, 'C#Pawn': 1, 'C#Cool': 1, 'C#Vim script': 1, 'C#Fortran': 1, 'C#Mathematica': 1, 'C#M': 1, 'C#SuperCollider': 1, 'C#Common Lisp': 1, 'C#AppleScript': 1, 'C#Mercury': 1, 'C#Pascal': 1, 'C#Forth': 1, 'C#RenderScript': 1, 'C#DTrace': 1, 'C#Logos': 1, 'RRoff': 3, 'RShaderLab': 1, 'RSwift': 2, 'RLua': 1, 'RHLSL': 1, 'RHack': 1, 'RLLVM': 1, 'RAssembly': 1, 'RCMake': 1, 'RCuda': 1, 'ROCaml': 1, 'RAwk': 1, 'RM4': 1, 'RTeX': 1, 'REmacs Lisp': 2, 'RSmalltalk': 1, 'RPawn': 1, 'RCool': 1, 'RVim script': 1, 'RFortran': 1, 'RMathematica': 1, 'RM': 1, 'RSuperCollider': 1, 'RCommon Lisp': 1, 'RAppleScript': 1, 'RMercury': 1, 'RPascal': 1, 'RForth': 1, 'RRenderScript': 1, 'RDTrace': 2, 'RLogos': 1, 'RoffShaderLab': 1, 'RoffSwift': 2, 'RoffLua': 1, 'RoffHLSL': 1, 'RoffHack': 1, 'RoffLLVM': 1, 'RoffAssembly': 1, 'RoffCMake': 1, 'RoffCuda': 1, 'RoffOCaml': 1, 'RoffAwk': 1, 'RoffM4': 1, 'RoffTeX': 1, 'RoffEmacs Lisp': 2, 'RoffSmalltalk': 1, 'RoffPawn': 1, 'RoffCool': 1, 'RoffVim script': 1, 'RoffFortran': 1, 'RoffMathematica': 1, 'RoffM': 1, 'RoffSuperCollider': 1, 'RoffCommon Lisp': 1, 'RoffAppleScript': 1, 'RoffMercury': 1, 'RoffPascal': 1, 'RoffForth': 1, 'RoffRenderScript': 1, 'RoffDTrace': 2, 'RoffLogos': 1, 'ShaderLabSwift': 1, 'ShaderLabLua': 1, 'ShaderLabHLSL': 1, 'ShaderLabHack': 1, 'SwiftLua': 1, 'SwiftHLSL': 1, 'SwiftHack': 1, 'SwiftLLVM': 1, 'SwiftAssembly': 1, 'SwiftCMake': 1, 'SwiftCuda': 1, 'SwiftOCaml': 1, 'SwiftAwk': 1, 'SwiftM4': 1, 'SwiftTeX': 1, 'SwiftEmacs Lisp': 1, 'SwiftSmalltalk': 1, 'SwiftPawn': 1, 'SwiftCool': 1, 'SwiftVim script': 1, 'SwiftFortran': 1, 'SwiftMathematica': 1, 'SwiftM': 1, 'SwiftSuperCollider': 1, 'SwiftCommon Lisp': 1, 'SwiftAppleScript': 1, 'SwiftMercury': 1, 'SwiftPascal': 1, 'SwiftForth': 1, 'SwiftRenderScript': 1, 'SwiftDTrace': 1, 'SwiftLogos': 1, 'LuaHLSL': 1, 'LuaHack': 1, 'HLSLHack': 1, 'LLVMAssembly': 1, 'LLVMCMake': 1, 'LLVMCuda': 1, 'LLVMOCaml': 1, 'LLVMAwk': 1, 'LLVMM4': 1, 'LLVMTeX': 1, 'LLVMEmacs Lisp': 1, 'LLVMSmalltalk': 1, 'LLVMPawn': 1, 'LLVMCool': 1, 'LLVMVim script': 1, 'LLVMFortran': 1, 'LLVMMathematica': 1, 'LLVMM': 1, 'LLVMSuperCollider': 1, 'LLVMCommon Lisp': 1, 'LLVMAppleScript': 1, 'LLVMMercury': 1, 'LLVMPascal': 1, 'LLVMForth': 1, 'LLVMRenderScript': 1, 'LLVMDTrace': 1, 'LLVMLogos': 1, 'AssemblyCMake': 1, 'AssemblyCuda': 1, 'AssemblyOCaml': 1, 'AssemblyAwk': 1, 'AssemblyM4': 1, 'AssemblyTeX': 1, 'AssemblyEmacs Lisp': 1, 'AssemblySmalltalk': 1, 'AssemblyPawn': 1, 'AssemblyCool': 1, 'AssemblyVim script': 1, 'AssemblyFortran': 1, 'AssemblyMathematica': 1, 'AssemblyM': 1, 'AssemblySuperCollider': 1, 'AssemblyCommon Lisp': 1, 'AssemblyAppleScript': 1, 'AssemblyMercury': 1, 'AssemblyPascal': 1, 'AssemblyForth': 1, 'AssemblyRenderScript': 1, 'AssemblyDTrace': 1, 'AssemblyLogos': 1, 'AssemblyV': 1, 'CMakeCuda': 1, 'CMakeOCaml': 1, 'CMakeAwk': 1, 'CMakeM4': 1, 'CMakeTeX': 1, 'CMakeEmacs Lisp': 1, 'CMakeSmalltalk': 1, 'CMakePawn': 1, 'CMakeCool': 1, 'CMakeVim script': 1, 'CMakeFortran': 1, 'CMakeMathematica': 1, 'CMakeM': 1, 'CMakeSuperCollider': 1, 'CMakeCommon Lisp': 1, 'CMakeAppleScript': 1, 'CMakeMercury': 1, 'CMakePascal': 1, 'CMakeForth': 1, 'CMakeRenderScript': 1, 'CMakeDTrace': 1, 'CMakeLogos': 1, 'CudaOCaml': 1, 'CudaAwk': 1, 'CudaM4': 1, 'CudaTeX': 1, 'CudaEmacs Lisp': 1, 'CudaSmalltalk': 1, 'CudaPawn': 1, 'CudaCool': 1, 'CudaVim script': 1, 'CudaFortran': 1, 'CudaMathematica': 1, 'CudaM': 1, 'CudaSuperCollider': 1, 'CudaCommon Lisp': 1, 'CudaAppleScript': 1, 'CudaMercury': 1, 'CudaPascal': 1, 'CudaForth': 1, 'CudaRenderScript': 1, 'CudaDTrace': 1, 'CudaLogos': 1, 'OCamlAwk': 1, 'OCamlM4': 1, 'OCamlTeX': 1, 'OCamlEmacs Lisp': 1, 'OCamlSmalltalk': 1, 'OCamlPawn': 1, 'OCamlCool': 1, 'OCamlVim script': 1, 'OCamlFortran': 1, 'OCamlMathematica': 1, 'OCamlM': 1, 'OCamlSuperCollider': 1, 'OCamlCommon Lisp': 1, 'OCamlAppleScript': 1, 'OCamlMercury': 1, 'OCamlPascal': 1, 'OCamlForth': 1, 'OCamlRenderScript': 1, 'OCamlDTrace': 1, 'OCamlLogos': 1, 'AwkM4': 1, 'AwkTeX': 1, 'AwkEmacs Lisp': 1, 'AwkSmalltalk': 1, 'AwkPawn': 1, 'AwkCool': 1, 'AwkVim script': 1, 'AwkFortran': 1, 'AwkMathematica': 1, 'AwkM': 1, 'AwkSuperCollider': 1, 'AwkCommon Lisp': 1, 'AwkAppleScript': 1, 'AwkMercury': 1, 'AwkPascal': 1, 'AwkForth': 1, 'AwkRenderScript': 1, 'AwkDTrace': 1, 'AwkLogos': 1, 'M4TeX': 1, 'M4Emacs Lisp': 1, 'M4Smalltalk': 1, 'M4Pawn': 1, 'M4Cool': 1, 'M4Vim script': 1, 'M4Fortran': 1, 'M4Mathematica': 1, 'M4M': 1, 'M4SuperCollider': 1, 'M4Common Lisp': 1, 'M4AppleScript': 1, 'M4Mercury': 1, 'M4Pascal': 1, 'M4Forth': 1, 'M4RenderScript': 1, 'M4DTrace': 1, 'M4Logos': 1, 'TeXEmacs Lisp': 1, 'TeXSmalltalk': 1, 'TeXPawn': 1, 'TeXCool': 1, 'TeXVim script': 1, 'TeXFortran': 1, 'TeXMathematica': 1, 'TeXM': 1, 'TeXSuperCollider': 1, 'TeXCommon Lisp': 1, 'TeXAppleScript': 1, 'TeXMercury': 1, 'TeXPascal': 1, 'TeXForth': 1, 'TeXRenderScript': 1, 'TeXDTrace': 1, 'TeXLogos': 1, 'Emacs LispSmalltalk': 1, 'Emacs LispPawn': 1, 'Emacs LispCool': 1, 'Emacs LispVim script': 1, 'Emacs LispFortran': 1, 'Emacs LispMathematica': 1, 'Emacs LispM': 1, 'Emacs LispSuperCollider': 1, 'Emacs LispCommon Lisp': 1, 'Emacs LispAppleScript': 1, 'Emacs LispMercury': 1, 'Emacs LispPascal': 1, 'Emacs LispForth': 1, 'Emacs LispRenderScript': 1, 'Emacs LispDTrace': 2, 'Emacs LispLogos': 1, 'SmalltalkPawn': 1, 'SmalltalkCool': 1, 'SmalltalkVim script': 1, 'SmalltalkFortran': 1, 'SmalltalkMathematica': 1, 'SmalltalkM': 1, 'SmalltalkSuperCollider': 1, 'SmalltalkCommon Lisp': 1, 'SmalltalkAppleScript': 1, 'SmalltalkMercury': 1, 'SmalltalkPascal': 1, 'SmalltalkForth': 1, 'SmalltalkRenderScript': 1, 'SmalltalkDTrace': 1, 'SmalltalkLogos': 1, 'PawnCool': 1, 'PawnVim script': 1, 'PawnFortran': 1, 'PawnMathematica': 1, 'PawnM': 1, 'PawnSuperCollider': 1, 'PawnCommon Lisp': 1, 'PawnAppleScript': 1, 'PawnMercury': 1, 'PawnPascal': 1, 'PawnForth': 1, 'PawnRenderScript': 1, 'PawnDTrace': 1, 'PawnLogos': 1, 'CoolVim script': 1, 'CoolFortran': 1, 'CoolMathematica': 1, 'CoolM': 1, 'CoolSuperCollider': 1, 'CoolCommon Lisp': 1, 'CoolAppleScript': 1, 'CoolMercury': 1, 'CoolPascal': 1, 'CoolForth': 1, 'CoolRenderScript': 1, 'CoolDTrace': 1, 'CoolLogos': 1, 'Vim scriptFortran': 1, 'Vim scriptMathematica': 1, 'Vim scriptM': 1, 'Vim scriptSuperCollider': 1, 'Vim scriptCommon Lisp': 1, 'Vim scriptAppleScript': 1, 'Vim scriptMercury': 1, 'Vim scriptPascal': 1, 'Vim scriptForth': 1, 'Vim scriptRenderScript': 1, 'Vim scriptDTrace': 1, 'Vim scriptLogos': 1, 'FortranMathematica': 1, 'FortranM': 1, 'FortranSuperCollider': 1, 'FortranCommon Lisp': 1, 'FortranAppleScript': 1, 'FortranMercury': 1, 'FortranPascal': 1, 'FortranForth': 1, 'FortranRenderScript': 1, 'FortranDTrace': 1, 'FortranLogos': 1, 'MathematicaM': 1, 'MathematicaSuperCollider': 1, 'MathematicaCommon Lisp': 1, 'MathematicaAppleScript': 1, 'MathematicaMercury': 1, 'MathematicaPascal': 1, 'MathematicaForth': 1, 'MathematicaRenderScript': 1, 'MathematicaDTrace': 1, 'MathematicaLogos': 1, 'MSuperCollider': 1, 'MCommon Lisp': 1, 'MAppleScript': 1, 'MMercury': 1, 'MPascal': 1, 'MForth': 1, 'MRenderScript': 1, 'MDTrace': 1, 'MLogos': 1, 'SuperColliderCommon Lisp': 1, 'SuperColliderAppleScript': 1, 'SuperColliderMercury': 1, 'SuperColliderPascal': 1, 'SuperColliderForth': 1, 'SuperColliderRenderScript': 1, 'SuperColliderDTrace': 1, 'SuperColliderLogos': 1, 'Common LispAppleScript': 1, 'Common LispMercury': 1, 'Common LispPascal': 1, 'Common LispForth': 1, 'Common LispRenderScript': 1, 'Common LispDTrace': 1, 'Common LispLogos': 1, 'AppleScriptMercury': 1, 'AppleScriptPascal': 1, 'AppleScriptForth': 1, 'AppleScriptRenderScript': 1, 'AppleScriptDTrace': 1, 'AppleScriptLogos': 1, 'MercuryPascal': 1, 'MercuryForth': 1, 'MercuryRenderScript': 1, 'MercuryDTrace': 1, 'MercuryLogos': 1, 'PascalForth': 1, 'PascalRenderScript': 1, 'PascalDTrace': 1, 'PascalLogos': 1, 'ForthRenderScript': 1, 'ForthDTrace': 1, 'ForthLogos': 1, 'RenderScriptDTrace': 1, 'RenderScriptLogos': 1, 'DTraceLogos': 1, 'VuePLpgSQL': 1, 'VueTSQL': 1, 'PLpgSQLTSQL': 1, 'ASPXSLT': 1, 'KotlinProlog': 1, 'KotlinFreeMarker': 1}


    for i in popdict.keys():
        if popdict[i] == max(popdict.values()):
            mode = i


    # Adding edges between langguages and repos
    for lang1 in langs_ids:
        # lang1name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang1[0]))
        for lang2 in langs_ids[langs_ids.index(lang1) + 1:]:
            if (lang1[0] != lang2[0]):
                # langpop = sqlconn.run('SELECT COUNT(repoid) FROM contains WHERE repoid=%d AND (langid=%d OR langid=%d);')
                try:
                    langpop = lang_dict[lang1[1] + lang2[1]]
                    if (langpop > mode):
                        tmp += '  edge [\n    source "' + lang1[1] +'"\n    target "' + lang2[1] +'"\n  ]\n'
                except:
                    pass
            # lang2name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang2[0]))
            # if (lang1name != lang2name):

    tmp += ']'
    filename = 'data/repos_langs_onemode.gml'
    with open(filename, 'w') as f:
        f.write(tmp)




def devLangOneModeToGml():
    tmp = 'graph [\n  directed 0\n'
    sqlconn = MySqlConn()
    langs = sqlconn.run('SELECT name FROM devlanguage;')
    langs_ids = []
    # Creating nodes for languages
    for lang in langs:
        langname = lang[0]
        langid = sqlconn.run('SELECT id FROM devlanguage WHERE name="%s";' %(langname))[0][0]
        langs_ids.append([langid, langname])
        tmp += '  node [\n    id "' + str(langname) + '"\n  ]\n'

    '''

    # Gathering the "repo share" data
    devs = sqlconn.run('SELECT username FROM dev;')
    popdict = {}
    lang_dict = {}
    for lang1 in langs_ids:
        print(lang1[0])
        # lang1name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang1[0]))
        for lang2 in langs_ids[langs_ids.index(lang1) + 1:]:
            if (lang1[0] != lang2[0]):
                reposshared = 0
                for username in devs:
                    username = username[0]
                    devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(username))[0][0]
                    langpop = sqlconn.run('SELECT COUNT(devid) FROM uses WHERE devid=%d AND (langid=%d OR langid=%d);' %(devid, lang1[0], lang2[0]))[0][0]
                    if(langpop > 1):
                        reposshared += 1
                        lang_dict[lang1[1] + lang2[1]] = reposshared
                        #print(langpop)
                if reposshared in popdict.keys():
                    popdict[reposshared] += 1
                else:
                    popdict[reposshared] = 1
    print(popdict)
    print(lang_dict)

    '''

    sqlconn.connection.close()

    popdict = {7: 31, 19: 1, 11: 11, 9: 11, 21: 3, 2: 248, 3: 167, 1: 978, 13: 14, 16: 7, 12: 4, 20: 1, 4: 63, 5: 39, 10: 14, 6: 24, 14: 5, 8: 9, 0: 1514, 23: 3, 22: 1, 15: 3, 25: 3, 17: 3, 24: 3}
    lang_dict = {'PythonVim script': 7, 'PythonMakefile': 19, 'PythonBatchfile': 11, 'PythonDockerfile': 9, 'PythonShell': 21, 'PythonAwk': 2, 'PythonPerl': 9, 'PythonMATLAB': 3, 'PythonM': 1, 'PythonC++': 13, 'PythonCuda': 1, 'PythonJupyter Notebook': 3, 'PythonCSS': 21, 'PythonHTML': 21, 'PythonTeX': 3, 'PythonPerl 6': 1, 'PythonC': 16, 'PythonProlog': 3, 'PythonJava': 12, 'PythonJavaScript': 20, 'PythonXML': 1, 'PythonKotlin': 4, 'PythonSwift': 5, 'PythonGroovy': 4, 'PythonANTLR': 1, 'PythonObjective-C': 13, 'PythonThrift': 2, 'PythonLex': 1, 'PythonGo': 10, 'PythonRust': 4, 'PythonScala': 5, 'PythonOCaml': 1, 'PythonPowerShell': 7, 'PythonAssembly': 3, 'PythonRoff': 7, 'PythonD': 1, 'PythonHaskell': 2, 'PythonIDL': 2, 'PythonYacc': 1, 'PythonC#': 7, 'PythonSmalltalk': 1, 'PythonObjective-C++': 6, 'PythonTcl': 1, 'PythonDIGITAL Command Language': 3, 'PythonSQLPL': 1, 'PythonTSQL': 1, 'PythonCMake': 3, 'PythonRuby': 14, 'PythonGLSL': 2, 'PythonTypeScript': 8, 'PythonAppleScript': 1, 'PythonCoffeeScript': 5, 'PythonProtocol Buffer': 1, 'PythonHCL': 3, 'PythonClojure': 3, 'PythonPHP': 3, 'PythonPostScript': 3, 'PythonDart': 3, 'PythonVisual Basic': 1, 'PythonXSLT': 3, 'Python1C Enterprise': 1, 'PythonOpenEdge ABL': 1, 'PythonASP': 1, 'PythonEmacs Lisp': 1, 'PythonLua': 2, 'Pythonsed': 2, 'PythonElm': 1, 'PythonNim': 1, 'PythonM4': 1, 'PythonRagel': 1, 'PythonPascal': 2, 'PythonAutoHotkey': 1, 'PythonNSIS': 1, 'PythonActionScript': 1, 'PythonApacheConf': 1, 'PythonSmarty': 1, 'PythonPLSQL': 1, 'PythonPuppet': 1, 'PythonTerra': 1, 'Vim scriptMakefile': 8, 'Vim scriptBatchfile': 3, 'Vim scriptDockerfile': 3, 'Vim scriptShell': 8, 'Vim scriptAwk': 1, 'Vim scriptPerl': 3, 'Vim scriptMATLAB': 1, 'Vim scriptM': 1, 'Vim scriptC++': 5, 'Vim scriptCuda': 1, 'Vim scriptJupyter Notebook': 2, 'Vim scriptCSS': 8, 'Vim scriptHTML': 8, 'Vim scriptTeX': 2, 'Vim scriptPerl 6': 1, 'Vim scriptC': 7, 'Vim scriptProlog': 1, 'Vim scriptJava': 3, 'Vim scriptJavaScript': 7, 'Vim scriptGroovy': 1, 'Vim scriptObjective-C': 2, 'Vim scriptGo': 4, 'Vim scriptRust': 2, 'Vim scriptScala': 1, 'Vim scriptPowerShell': 2, 'Vim scriptRoff': 1, 'Vim scriptYacc': 1, 'Vim scriptC#': 2, 'Vim scriptObjective-C++': 1, 'Vim scriptDIGITAL Command Language': 1, 'Vim scriptCMake': 2, 'Vim scriptRuby': 2, 'Vim scriptTypeScript': 2, 'Vim scriptAppleScript': 1, 'Vim scriptCoffeeScript': 1, 'Vim scriptHCL': 1, 'Vim scriptClojure': 1, 'Vim scriptPHP': 1, 'Vim scriptPostScript': 1, 'Vim scriptDart': 1, 'Vim scriptVisual Basic': 1, 'Vim scriptXSLT': 1, 'Vim script1C Enterprise': 1, 'Vim scriptOpenEdge ABL': 1, 'Vim scriptASP': 1, 'Vim scriptEmacs Lisp': 1, 'Vim scriptLua': 2, 'Vim scriptTerra': 1, 'MakefileBatchfile': 10, 'MakefileDockerfile': 11, 'MakefileShell': 23, 'MakefileAwk': 2, 'MakefilePerl': 10, 'MakefileMATLAB': 3, 'MakefileM': 1, 'MakefileC++': 14, 'MakefileCuda': 1, 'MakefileJupyter Notebook': 3, 'MakefileCSS': 23, 'MakefileHTML': 23, 'MakefileTeX': 3, 'MakefilePerl 6': 1, 'MakefileC': 16, 'MakefileProlog': 3, 'MakefileJava': 12, 'MakefileJavaScript': 22, 'MakefileXML': 1, 'MakefileKotlin': 4, 'MakefileSwift': 5, 'MakefileGroovy': 4, 'MakefileANTLR': 1, 'MakefileObjective-C': 11, 'MakefileThrift': 2, 'MakefileLex': 1, 'MakefileGo': 13, 'MakefileRust': 4, 'MakefileScala': 5, 'MakefileOCaml': 2, 'MakefilePowerShell': 7, 'MakefileAssembly': 3, 'MakefileRoff': 7, 'MakefileD': 1, 'MakefileHaskell': 2, 'MakefileIDL': 2, 'MakefileYacc': 2, 'MakefileC#': 6, 'MakefileSmalltalk': 1, 'MakefileObjective-C++': 5, 'MakefileTcl': 1, 'MakefileDIGITAL Command Language': 3, 'MakefileSQLPL': 1, 'MakefileTSQL': 1, 'MakefileCMake': 4, 'MakefileRuby': 14, 'MakefileGLSL': 2, 'MakefileTypeScript': 9, 'MakefileAppleScript': 2, 'MakefileCoffeeScript': 3, 'MakefileHCL': 3, 'MakefileClojure': 3, 'MakefilePHP': 4, 'MakefilePostScript': 3, 'MakefileDart': 3, 'MakefileVisual Basic': 1, 'MakefileXSLT': 3, 'Makefile1C Enterprise': 1, 'MakefileOpenEdge ABL': 1, 'MakefileASP': 1, 'MakefileEmacs Lisp': 1, 'MakefileLua': 3, 'Makefilesed': 2, 'MakefileElm': 1, 'MakefileNim': 1, 'MakefileM4': 1, 'MakefileRagel': 1, 'MakefilePascal': 2, 'MakefileAutoHotkey': 1, 'MakefileNSIS': 1, 'MakefileActionScript': 1, 'MakefileApacheConf': 1, 'MakefileSmarty': 1, 'MakefilePLSQL': 1, 'MakefilePuppet': 1, 'MakefileTerra': 1, 'BatchfileDockerfile': 6, 'BatchfileShell': 11, 'BatchfileAwk': 2, 'BatchfilePerl': 5, 'BatchfileMATLAB': 2, 'BatchfileM': 1, 'BatchfileC++': 9, 'BatchfileCuda': 1, 'BatchfileJupyter Notebook': 2, 'BatchfileCSS': 11, 'BatchfileHTML': 11, 'BatchfileTeX': 3, 'BatchfilePerl 6': 1, 'BatchfileC': 9, 'BatchfileProlog': 3, 'BatchfileJava': 8, 'BatchfileJavaScript': 10, 'BatchfileXML': 1, 'BatchfileKotlin': 4, 'BatchfileSwift': 3, 'BatchfileGroovy': 3, 'BatchfileANTLR': 1, 'BatchfileObjective-C': 9, 'BatchfileThrift': 1, 'BatchfileLex': 1, 'BatchfileGo': 5, 'BatchfileRust': 3, 'BatchfileScala': 4, 'BatchfileOCaml': 1, 'BatchfilePowerShell': 6, 'BatchfileAssembly': 3, 'BatchfileRoff': 6, 'BatchfileD': 1, 'BatchfileHaskell': 2, 'BatchfileIDL': 2, 'BatchfileYacc': 1, 'BatchfileC#': 5, 'BatchfileSmalltalk': 1, 'BatchfileObjective-C++': 5, 'BatchfileTcl': 1, 'BatchfileDIGITAL Command Language': 3, 'BatchfileSQLPL': 1, 'BatchfileTSQL': 1, 'BatchfileCMake': 3, 'BatchfileRuby': 8, 'BatchfileGLSL': 2, 'BatchfileTypeScript': 5, 'BatchfileCoffeeScript': 2, 'BatchfileProtocol Buffer': 1, 'BatchfileClojure': 3, 'BatchfilePHP': 1, 'BatchfilePostScript': 2, 'BatchfileDart': 3, 'BatchfileVisual Basic': 1, 'BatchfileXSLT': 3, 'Batchfile1C Enterprise': 1, 'BatchfileOpenEdge ABL': 1, 'BatchfileASP': 1, 'BatchfileEmacs Lisp': 1, 'BatchfileLua': 2, 'Batchfilesed': 2, 'BatchfileElm': 1, 'BatchfileNim': 1, 'BatchfileM4': 1, 'BatchfileRagel': 1, 'BatchfilePascal': 1, 'BatchfileAutoHotkey': 1, 'BatchfileNSIS': 1, 'BatchfileActionScript': 1, 'BatchfileApacheConf': 1, 'BatchfileSmarty': 1, 'DockerfileShell': 11, 'DockerfileAwk': 1, 'DockerfilePerl': 2, 'DockerfileMATLAB': 2, 'DockerfileM': 1, 'DockerfileC++': 7, 'DockerfileCuda': 1, 'DockerfileJupyter Notebook': 2, 'DockerfileCSS': 11, 'DockerfileHTML': 11, 'DockerfileTeX': 3, 'DockerfilePerl 6': 1, 'DockerfileC': 7, 'DockerfileProlog': 2, 'DockerfileJava': 7, 'DockerfileJavaScript': 10, 'DockerfileXML': 1, 'DockerfileKotlin': 3, 'DockerfileSwift': 4, 'DockerfileGroovy': 1, 'DockerfileANTLR': 1, 'DockerfileObjective-C': 6, 'DockerfileThrift': 1, 'DockerfileLex': 1, 'DockerfileGo': 7, 'DockerfileRust': 3, 'DockerfileScala': 3, 'DockerfileOCaml': 2, 'DockerfilePowerShell': 4, 'DockerfileAssembly': 2, 'DockerfileRoff': 3, 'DockerfileD': 1, 'DockerfileHaskell': 1, 'DockerfileIDL': 1, 'DockerfileYacc': 1, 'DockerfileC#': 3, 'DockerfileSmalltalk': 1, 'DockerfileObjective-C++': 2, 'DockerfileTcl': 1, 'DockerfileDIGITAL Command Language': 1, 'DockerfileSQLPL': 1, 'DockerfileTSQL': 1, 'DockerfileCMake': 1, 'DockerfileRuby': 7, 'DockerfileGLSL': 1, 'DockerfileTypeScript': 5, 'DockerfileAppleScript': 2, 'DockerfileHCL': 2, 'DockerfileClojure': 1, 'DockerfilePHP': 1, 'DockerfilePostScript': 1, 'DockerfileDart': 2, 'DockerfileXSLT': 1, 'DockerfileEmacs Lisp': 1, 'DockerfileLua': 1, 'Dockerfilesed': 1, 'DockerfileElm': 1, 'DockerfilePascal': 1, 'DockerfilePLSQL': 1, 'DockerfilePuppet': 1, 'ShellAwk': 2, 'ShellPerl': 10, 'ShellMATLAB': 3, 'ShellM': 1, 'ShellC++': 15, 'ShellCuda': 1, 'ShellJupyter Notebook': 3, 'ShellCSS': 25, 'ShellHTML': 25, 'ShellTeX': 3, 'ShellPerl 6': 1, 'ShellC': 17, 'ShellProlog': 3, 'ShellJava': 13, 'ShellJavaScript': 24, 'ShellXML': 1, 'ShellKotlin': 4, 'ShellSwift': 5, 'ShellGroovy': 4, 'ShellANTLR': 1, 'ShellObjective-C': 13, 'ShellThrift': 2, 'ShellLex': 1, 'ShellGo': 13, 'ShellRust': 5, 'ShellScala': 5, 'ShellOCaml': 2, 'ShellPowerShell': 7, 'ShellAssembly': 3, 'ShellRoff': 7, 'ShellD': 1, 'ShellHaskell': 2, 'ShellIDL': 2, 'ShellYacc': 2, 'ShellC#': 7, 'ShellSmalltalk': 1, 'ShellObjective-C++': 6, 'ShellTcl': 1, 'ShellDIGITAL Command Language': 3, 'ShellSQLPL': 1, 'ShellTSQL': 1, 'ShellCMake': 4, 'ShellRuby': 16, 'ShellGLSL': 2, 'ShellTypeScript': 10, 'ShellAppleScript': 2, 'ShellCoffeeScript': 5, 'ShellProtocol Buffer': 1, 'ShellHCL': 3, 'ShellClojure': 3, 'ShellPHP': 4, 'ShellPostScript': 3, 'ShellDart': 3, 'ShellVisual Basic': 1, 'ShellXSLT': 3, 'Shell1C Enterprise': 1, 'ShellOpenEdge ABL': 1, 'ShellASP': 1, 'ShellEmacs Lisp': 1, 'ShellLua': 3, 'Shellsed': 2, 'ShellElm': 1, 'ShellNim': 1, 'ShellM4': 1, 'ShellRagel': 1, 'ShellPascal': 2, 'ShellAutoHotkey': 1, 'ShellNSIS': 1, 'ShellActionScript': 1, 'ShellApacheConf': 1, 'ShellSmarty': 1, 'ShellPLSQL': 1, 'ShellPuppet': 1, 'ShellTerra': 1, 'AwkPerl': 2, 'AwkMATLAB': 1, 'AwkM': 1, 'AwkC++': 2, 'AwkCuda': 1, 'AwkJupyter Notebook': 1, 'AwkCSS': 2, 'AwkHTML': 2, 'AwkTeX': 1, 'AwkPerl 6': 1, 'AwkC': 2, 'AwkProlog': 1, 'AwkJava': 2, 'AwkJavaScript': 1, 'AwkGroovy': 1, 'AwkObjective-C': 1, 'AwkRoff': 1, 'AwkC#': 1, 'AwkDIGITAL Command Language': 1, 'AwkCMake': 1, 'AwkRuby': 1, 'AwkGLSL': 1, 'Awksed': 1, 'AwkNim': 1, 'AwkM4': 1, 'AwkRagel': 1, 'PerlMATLAB': 2, 'PerlM': 1, 'PerlC++': 7, 'PerlCuda': 1, 'PerlJupyter Notebook': 2, 'PerlCSS': 10, 'PerlHTML': 10, 'PerlTeX': 1, 'PerlPerl 6': 1, 'PerlC': 7, 'PerlProlog': 2, 'PerlJava': 6, 'PerlJavaScript': 9, 'PerlKotlin': 1, 'PerlSwift': 1, 'PerlGroovy': 3, 'PerlObjective-C': 5, 'PerlThrift': 1, 'PerlGo': 5, 'PerlRust': 1, 'PerlScala': 2, 'PerlPowerShell': 2, 'PerlAssembly': 1, 'PerlRoff': 4, 'PerlHaskell': 1, 'PerlIDL': 1, 'PerlYacc': 1, 'PerlC#': 3, 'PerlObjective-C++': 3, 'PerlDIGITAL Command Language': 2, 'PerlCMake': 3, 'PerlRuby': 6, 'PerlGLSL': 1, 'PerlTypeScript': 3, 'PerlCoffeeScript': 3, 'PerlHCL': 1, 'PerlClojure': 2, 'PerlPHP': 2, 'PerlPostScript': 2, 'PerlDart': 1, 'PerlVisual Basic': 1, 'PerlXSLT': 2, 'Perl1C Enterprise': 1, 'PerlOpenEdge ABL': 1, 'PerlASP': 1, 'PerlLua': 2, 'Perlsed': 1, 'PerlNim': 1, 'PerlM4': 1, 'PerlRagel': 1, 'PerlPascal': 2, 'PerlAutoHotkey': 1, 'PerlNSIS': 1, 'PerlActionScript': 1, 'PerlApacheConf': 1, 'PerlSmarty': 1, 'PerlPLSQL': 1, 'PerlPuppet': 1, 'MATLABM': 1, 'MATLABC++': 2, 'MATLABCuda': 1, 'MATLABJupyter Notebook': 1, 'MATLABCSS': 3, 'MATLABHTML': 3, 'MATLABTeX': 1, 'MATLABPerl 6': 1, 'MATLABC': 2, 'MATLABProlog': 2, 'MATLABJava': 3, 'MATLABJavaScript': 2, 'MATLABXML': 1, 'MATLABKotlin': 1, 'MATLABSwift': 1, 'MATLABGroovy': 2, 'MATLABANTLR': 1, 'MATLABObjective-C': 1, 'MATLABThrift': 1, 'MATLABLex': 1, 'MATLABGo': 2, 'MATLABRust': 1, 'MATLABScala': 1, 'MATLABOCaml': 1, 'MATLABPowerShell': 1, 'MATLABAssembly': 1, 'MATLABRoff': 1, 'MATLABD': 1, 'MATLABHaskell': 1, 'MATLABIDL': 1, 'MATLABYacc': 1, 'MATLABC#': 2, 'MATLABSmalltalk': 1, 'MATLABObjective-C++': 1, 'MATLABRuby': 1, 'MATLABCoffeeScript': 1, 'MC++': 1, 'MCuda': 1, 'MJupyter Notebook': 1, 'MCSS': 1, 'MHTML': 1, 'MTeX': 1, 'MPerl 6': 1, 'MC': 1, 'MProlog': 1, 'MJava': 1, 'C++Cuda': 1, 'C++Jupyter Notebook': 2, 'C++CSS': 15, 'C++HTML': 15, 'C++TeX': 2, 'C++Perl 6': 1, 'C++C': 14, 'C++Prolog': 3, 'C++Java': 10, 'C++JavaScript': 14, 'C++XML': 1, 'C++Kotlin': 4, 'C++Swift': 3, 'C++Groovy': 3, 'C++ANTLR': 1, 'C++Objective-C': 11, 'C++Thrift': 2, 'C++Lex': 1, 'C++Go': 7, 'C++Rust': 4, 'C++Scala': 4, 'C++OCaml': 2, 'C++PowerShell': 6, 'C++Assembly': 3, 'C++Roff': 6, 'C++D': 1, 'C++Haskell': 2, 'C++IDL': 2, 'C++Yacc': 2, 'C++C#': 5, 'C++Smalltalk': 1, 'C++Objective-C++': 6, 'C++Tcl': 1, 'C++DIGITAL Command Language': 3, 'C++SQLPL': 1, 'C++TSQL': 1, 'C++CMake': 4, 'C++Ruby': 9, 'C++GLSL': 2, 'C++TypeScript': 6, 'C++AppleScript': 2, 'C++CoffeeScript': 2, 'C++Clojure': 3, 'C++PHP': 2, 'C++PostScript': 1, 'C++Dart': 3, 'C++Visual Basic': 1, 'C++XSLT': 3, 'C++1C Enterprise': 1, 'C++OpenEdge ABL': 1, 'C++ASP': 1, 'C++Lua': 2, 'C++sed': 2, 'C++Elm': 1, 'C++Nim': 1, 'C++M4': 1, 'C++Ragel': 1, 'C++Pascal': 1, 'C++AutoHotkey': 1, 'C++NSIS': 1, 'C++ActionScript': 1, 'C++ApacheConf': 1, 'C++Smarty': 1, 'C++Terra': 1, 'CudaJupyter Notebook': 1, 'CudaCSS': 1, 'CudaHTML': 1, 'CudaTeX': 1, 'CudaPerl 6': 1, 'CudaC': 1, 'CudaProlog': 1, 'CudaJava': 1, 'Jupyter NotebookCSS': 3, 'Jupyter NotebookHTML': 3, 'Jupyter NotebookTeX': 2, 'Jupyter NotebookPerl 6': 1, 'Jupyter NotebookC': 2, 'Jupyter NotebookProlog': 1, 'Jupyter NotebookJava': 2, 'Jupyter NotebookJavaScript': 2, 'Jupyter NotebookObjective-C': 1, 'Jupyter NotebookThrift': 1, 'Jupyter NotebookGo': 1, 'Jupyter NotebookRust': 1, 'Jupyter NotebookScala': 2, 'Jupyter NotebookRuby': 1, 'Jupyter NotebookPostScript': 1, 'Jupyter NotebookEmacs Lisp': 1, 'Jupyter NotebookLua': 1, 'CSSHTML': 25, 'CSSTeX': 3, 'CSSPerl 6': 1, 'CSSC': 17, 'CSSProlog': 3, 'CSSJava': 13, 'CSSJavaScript': 24, 'CSSXML': 1, 'CSSKotlin': 4, 'CSSSwift': 5, 'CSSGroovy': 4, 'CSSANTLR': 1, 'CSSObjective-C': 13, 'CSSThrift': 2, 'CSSLex': 1, 'CSSGo': 13, 'CSSRust': 5, 'CSSScala': 5, 'CSSOCaml': 2, 'CSSPowerShell': 7, 'CSSAssembly': 3, 'CSSRoff': 7, 'CSSD': 1, 'CSSHaskell': 2, 'CSSIDL': 2, 'CSSYacc': 2, 'CSSC#': 7, 'CSSSmalltalk': 1, 'CSSObjective-C++': 6, 'CSSTcl': 1, 'CSSDIGITAL Command Language': 3, 'CSSSQLPL': 1, 'CSSTSQL': 1, 'CSSCMake': 4, 'CSSRuby': 16, 'CSSGLSL': 2, 'CSSTypeScript': 10, 'CSSAppleScript': 2, 'CSSCoffeeScript': 5, 'CSSProtocol Buffer': 1, 'CSSHCL': 3, 'CSSClojure': 3, 'CSSPHP': 4, 'CSSPostScript': 3, 'CSSDart': 3, 'CSSVisual Basic': 1, 'CSSXSLT': 3, 'CSS1C Enterprise': 1, 'CSSOpenEdge ABL': 1, 'CSSASP': 1, 'CSSEmacs Lisp': 1, 'CSSLua': 3, 'CSSsed': 2, 'CSSElm': 1, 'CSSNim': 1, 'CSSM4': 1, 'CSSRagel': 1, 'CSSPascal': 2, 'CSSAutoHotkey': 1, 'CSSNSIS': 1, 'CSSActionScript': 1, 'CSSApacheConf': 1, 'CSSSmarty': 1, 'CSSPLSQL': 1, 'CSSPuppet': 1, 'CSSTerra': 1, 'HTMLTeX': 3, 'HTMLPerl 6': 1, 'HTMLC': 17, 'HTMLProlog': 3, 'HTMLJava': 13, 'HTMLJavaScript': 24, 'HTMLXML': 1, 'HTMLKotlin': 4, 'HTMLSwift': 5, 'HTMLGroovy': 4, 'HTMLANTLR': 1, 'HTMLObjective-C': 13, 'HTMLThrift': 2, 'HTMLLex': 1, 'HTMLGo': 13, 'HTMLRust': 5, 'HTMLScala': 5, 'HTMLOCaml': 2, 'HTMLPowerShell': 7, 'HTMLAssembly': 3, 'HTMLRoff': 7, 'HTMLD': 1, 'HTMLHaskell': 2, 'HTMLIDL': 2, 'HTMLYacc': 2, 'HTMLC#': 7, 'HTMLSmalltalk': 1, 'HTMLObjective-C++': 6, 'HTMLTcl': 1, 'HTMLDIGITAL Command Language': 3, 'HTMLSQLPL': 1, 'HTMLTSQL': 1, 'HTMLCMake': 4, 'HTMLRuby': 16, 'HTMLGLSL': 2, 'HTMLTypeScript': 10, 'HTMLAppleScript': 2, 'HTMLCoffeeScript': 5, 'HTMLProtocol Buffer': 1, 'HTMLHCL': 3, 'HTMLClojure': 3, 'HTMLPHP': 4, 'HTMLPostScript': 3, 'HTMLDart': 3, 'HTMLVisual Basic': 1, 'HTMLXSLT': 3, 'HTML1C Enterprise': 1, 'HTMLOpenEdge ABL': 1, 'HTMLASP': 1, 'HTMLEmacs Lisp': 1, 'HTMLLua': 3, 'HTMLsed': 2, 'HTMLElm': 1, 'HTMLNim': 1, 'HTMLM4': 1, 'HTMLRagel': 1, 'HTMLPascal': 2, 'HTMLAutoHotkey': 1, 'HTMLNSIS': 1, 'HTMLActionScript': 1, 'HTMLApacheConf': 1, 'HTMLSmarty': 1, 'HTMLPLSQL': 1, 'HTMLPuppet': 1, 'HTMLTerra': 1, 'TeXPerl 6': 1, 'TeXC': 2, 'TeXProlog': 1, 'TeXJava': 2, 'TeXJavaScript': 2, 'TeXObjective-C': 1, 'TeXGo': 2, 'TeXRust': 1, 'TeXScala': 1, 'TeXPowerShell': 1, 'TeXAssembly': 1, 'TeXRoff': 1, 'TeXC#': 1, 'TeXTcl': 1, 'TeXDIGITAL Command Language': 1, 'TeXSQLPL': 1, 'TeXTSQL': 1, 'TeXCMake': 1, 'TeXRuby': 2, 'TeXGLSL': 1, 'TeXPostScript': 1, 'TeXEmacs Lisp': 1, 'TeXLua': 1, 'Perl 6C': 1, 'Perl 6Prolog': 1, 'Perl 6Java': 1, 'CProlog': 3, 'CJava': 11, 'CJavaScript': 16, 'CXML': 1, 'CKotlin': 4, 'CSwift': 4, 'CGroovy': 3, 'CANTLR': 1, 'CObjective-C': 12, 'CThrift': 2, 'CLex': 1, 'CGo': 7, 'CRust': 4, 'CScala': 4, 'COCaml': 1, 'CPowerShell': 7, 'CAssembly': 3, 'CRoff': 6, 'CD': 1, 'CHaskell': 2, 'CIDL': 2, 'CYacc': 2, 'CC#': 5, 'CSmalltalk': 1, 'CObjective-C++': 6, 'CTcl': 1, 'CDIGITAL Command Language': 3, 'CSQLPL': 1, 'CTSQL': 1, 'CCMake': 4, 'CRuby': 9, 'CGLSL': 2, 'CTypeScript': 6, 'CAppleScript': 1, 'CCoffeeScript': 2, 'CHCL': 2, 'CClojure': 3, 'CPHP': 2, 'CPostScript': 1, 'CDart': 3, 'CVisual Basic': 1, 'CXSLT': 3, 'C1C Enterprise': 1, 'COpenEdge ABL': 1, 'CASP': 1, 'CLua': 2, 'Csed': 2, 'CElm': 1, 'CNim': 1, 'CM4': 1, 'CRagel': 1, 'CPascal': 1, 'CAutoHotkey': 1, 'CNSIS': 1, 'CActionScript': 1, 'CApacheConf': 1, 'CSmarty': 1, 'CTerra': 1, 'PrologJava': 3, 'PrologJavaScript': 2, 'PrologXML': 1, 'PrologKotlin': 2, 'PrologSwift': 1, 'PrologGroovy': 1, 'PrologANTLR': 1, 'PrologObjective-C': 2, 'PrologThrift': 1, 'PrologLex': 1, 'PrologGo': 1, 'PrologRust': 1, 'PrologScala': 1, 'PrologOCaml': 1, 'PrologPowerShell': 1, 'PrologAssembly': 2, 'PrologRoff': 1, 'PrologD': 1, 'PrologHaskell': 2, 'PrologIDL': 2, 'PrologYacc': 1, 'PrologC#': 1, 'PrologSmalltalk': 1, 'PrologObjective-C++': 2, 'PrologRuby': 1, 'PrologClojure': 1, 'JavaJavaScript': 12, 'JavaXML': 1, 'JavaKotlin': 4, 'JavaSwift': 4, 'JavaGroovy': 3, 'JavaANTLR': 1, 'JavaObjective-C': 10, 'JavaThrift': 2, 'JavaLex': 1, 'JavaGo': 5, 'JavaRust': 3, 'JavaScala': 3, 'JavaOCaml': 1, 'JavaPowerShell': 4, 'JavaAssembly': 3, 'JavaRoff': 4, 'JavaD': 1, 'JavaHaskell': 2, 'JavaIDL': 2, 'JavaYacc': 2, 'JavaC#': 6, 'JavaSmalltalk': 1, 'JavaObjective-C++': 3, 'JavaTcl': 1, 'JavaDIGITAL Command Language': 2, 'JavaSQLPL': 1, 'JavaTSQL': 1, 'JavaCMake': 3, 'JavaRuby': 8, 'JavaGLSL': 2, 'JavaTypeScript': 5, 'JavaAppleScript': 1, 'JavaCoffeeScript': 2, 'JavaProtocol Buffer': 1, 'JavaHCL': 1, 'JavaClojure': 2, 'JavaDart': 2, 'JavaXSLT': 1, 'JavaLua': 1, 'Javased': 2, 'JavaElm': 1, 'JavaNim': 1, 'JavaM4': 1, 'JavaRagel': 1, 'JavaScriptXML': 1, 'JavaScriptKotlin': 4, 'JavaScriptSwift': 5, 'JavaScriptGroovy': 4, 'JavaScriptANTLR': 1, 'JavaScriptObjective-C': 13, 'JavaScriptThrift': 2, 'JavaScriptLex': 1, 'JavaScriptGo': 13, 'JavaScriptRust': 5, 'JavaScriptScala': 5, 'JavaScriptOCaml': 2, 'JavaScriptPowerShell': 7, 'JavaScriptAssembly': 3, 'JavaScriptRoff': 7, 'JavaScriptD': 1, 'JavaScriptHaskell': 2, 'JavaScriptIDL': 2, 'JavaScriptYacc': 2, 'JavaScriptC#': 7, 'JavaScriptSmalltalk': 1, 'JavaScriptObjective-C++': 6, 'JavaScriptTcl': 1, 'JavaScriptDIGITAL Command Language': 3, 'JavaScriptSQLPL': 1, 'JavaScriptTSQL': 1, 'JavaScriptCMake': 4, 'JavaScriptRuby': 16, 'JavaScriptGLSL': 2, 'JavaScriptTypeScript': 10, 'JavaScriptAppleScript': 2, 'JavaScriptCoffeeScript': 5, 'JavaScriptProtocol Buffer': 1, 'JavaScriptHCL': 3, 'JavaScriptClojure': 3, 'JavaScriptPHP': 4, 'JavaScriptPostScript': 3, 'JavaScriptDart': 3, 'JavaScriptVisual Basic': 1, 'JavaScriptXSLT': 3, 'JavaScript1C Enterprise': 1, 'JavaScriptOpenEdge ABL': 1, 'JavaScriptASP': 1, 'JavaScriptEmacs Lisp': 1, 'JavaScriptLua': 3, 'JavaScriptsed': 2, 'JavaScriptElm': 1, 'JavaScriptNim': 1, 'JavaScriptM4': 1, 'JavaScriptRagel': 1, 'JavaScriptPascal': 2, 'JavaScriptAutoHotkey': 1, 'JavaScriptNSIS': 1, 'JavaScriptActionScript': 1, 'JavaScriptApacheConf': 1, 'JavaScriptSmarty': 1, 'JavaScriptPLSQL': 1, 'JavaScriptPuppet': 1, 'JavaScriptTerra': 1, 'XMLKotlin': 1, 'XMLSwift': 1, 'XMLGroovy': 1, 'XMLANTLR': 1, 'XMLObjective-C': 1, 'XMLThrift': 1, 'XMLLex': 1, 'XMLGo': 1, 'XMLRust': 1, 'XMLScala': 1, 'XMLOCaml': 1, 'XMLPowerShell': 1, 'XMLAssembly': 1, 'XMLRoff': 1, 'XMLD': 1, 'XMLHaskell': 1, 'XMLIDL': 1, 'XMLYacc': 1, 'XMLC#': 1, 'XMLSmalltalk': 1, 'XMLObjective-C++': 1, 'KotlinSwift': 3, 'KotlinGroovy': 1, 'KotlinANTLR': 1, 'KotlinObjective-C': 4, 'KotlinThrift': 1, 'KotlinLex': 1, 'KotlinGo': 2, 'KotlinRust': 2, 'KotlinScala': 2, 'KotlinOCaml': 1, 'KotlinPowerShell': 3, 'KotlinAssembly': 2, 'KotlinRoff': 2, 'KotlinD': 1, 'KotlinHaskell': 2, 'KotlinIDL': 2, 'KotlinYacc': 1, 'KotlinC#': 1, 'KotlinSmalltalk': 1, 'KotlinObjective-C++': 3, 'KotlinRuby': 3, 'KotlinTypeScript': 2, 'KotlinClojure': 2, 'KotlinDart': 2, 'KotlinXSLT': 1, 'Kotlinsed': 1, 'KotlinElm': 1, 'SwiftGroovy': 1, 'SwiftANTLR': 1, 'SwiftObjective-C': 4, 'SwiftThrift': 1, 'SwiftLex': 1, 'SwiftGo': 3, 'SwiftRust': 2, 'SwiftScala': 2, 'SwiftOCaml': 1, 'SwiftPowerShell': 3, 'SwiftAssembly': 1, 'SwiftRoff': 3, 'SwiftD': 1, 'SwiftHaskell': 1, 'SwiftIDL': 1, 'SwiftYacc': 1, 'SwiftC#': 1, 'SwiftSmalltalk': 1, 'SwiftObjective-C++': 2, 'SwiftRuby': 4, 'SwiftTypeScript': 4, 'SwiftCoffeeScript': 1, 'SwiftHCL': 1, 'SwiftClojure': 1, 'SwiftPHP': 1, 'SwiftPostScript': 1, 'SwiftDart': 2, 'SwiftXSLT': 1, 'Swiftsed': 1, 'SwiftElm': 1, 'GroovyANTLR': 1, 'GroovyObjective-C': 3, 'GroovyThrift': 1, 'GroovyLex': 1, 'GroovyGo': 2, 'GroovyRust': 1, 'GroovyScala': 1, 'GroovyOCaml': 1, 'GroovyPowerShell': 2, 'GroovyAssembly': 1, 'GroovyRoff': 3, 'GroovyD': 1, 'GroovyHaskell': 1, 'GroovyIDL': 1, 'GroovyYacc': 1, 'GroovyC#': 4, 'GroovySmalltalk': 1, 'GroovyObjective-C++': 2, 'GroovyDIGITAL Command Language': 2, 'GroovyCMake': 2, 'GroovyRuby': 2, 'GroovyGLSL': 1, 'GroovyTypeScript': 1, 'GroovyCoffeeScript': 2, 'GroovyClojure': 1, 'GroovyDart': 1, 'GroovyVisual Basic': 1, 'GroovyXSLT': 1, 'Groovy1C Enterprise': 1, 'GroovyOpenEdge ABL': 1, 'GroovyASP': 1, 'Groovysed': 1, 'GroovyNim': 1, 'GroovyM4': 1, 'GroovyRagel': 1, 'ANTLRObjective-C': 1, 'ANTLRThrift': 1, 'ANTLRLex': 1, 'ANTLRGo': 1, 'ANTLRRust': 1, 'ANTLRScala': 1, 'ANTLROCaml': 1, 'ANTLRPowerShell': 1, 'ANTLRAssembly': 1, 'ANTLRRoff': 1, 'ANTLRD': 1, 'ANTLRHaskell': 1, 'ANTLRIDL': 1, 'ANTLRYacc': 1, 'ANTLRC#': 1, 'ANTLRSmalltalk': 1, 'ANTLRObjective-C++': 1, 'Objective-CThrift': 2, 'Objective-CLex': 1, 'Objective-CGo': 4, 'Objective-CRust': 3, 'Objective-CScala': 4, 'Objective-COCaml': 1, 'Objective-CPowerShell': 6, 'Objective-CAssembly': 3, 'Objective-CRoff': 6, 'Objective-CD': 1, 'Objective-CHaskell': 2, 'Objective-CIDL': 2, 'Objective-CYacc': 1, 'Objective-CC#': 6, 'Objective-CSmalltalk': 1, 'Objective-CObjective-C++': 6, 'Objective-CTcl': 1, 'Objective-CDIGITAL Command Language': 3, 'Objective-CSQLPL': 1, 'Objective-CTSQL': 1, 'Objective-CCMake': 3, 'Objective-CRuby': 9, 'Objective-CGLSL': 2, 'Objective-CTypeScript': 7, 'Objective-CAppleScript': 1, 'Objective-CCoffeeScript': 3, 'Objective-CProtocol Buffer': 1, 'Objective-CHCL': 1, 'Objective-CClojure': 3, 'Objective-CPHP': 1, 'Objective-CPostScript': 1, 'Objective-CDart': 3, 'Objective-CVisual Basic': 1, 'Objective-CXSLT': 3, 'Objective-C1C Enterprise': 1, 'Objective-COpenEdge ABL': 1, 'Objective-CASP': 1, 'Objective-CLua': 1, 'Objective-Csed': 2, 'Objective-CElm': 1, 'Objective-CNim': 1, 'Objective-CM4': 1, 'Objective-CRagel': 1, 'Objective-CPascal': 1, 'Objective-CAutoHotkey': 1, 'Objective-CNSIS': 1, 'Objective-CActionScript': 1, 'Objective-CApacheConf': 1, 'Objective-CSmarty': 1, 'ThriftLex': 1, 'ThriftGo': 1, 'ThriftRust': 1, 'ThriftScala': 2, 'ThriftOCaml': 1, 'ThriftPowerShell': 1, 'ThriftAssembly': 1, 'ThriftRoff': 1, 'ThriftD': 1, 'ThriftHaskell': 1, 'ThriftIDL': 1, 'ThriftYacc': 1, 'ThriftC#': 1, 'ThriftSmalltalk': 1, 'ThriftObjective-C++': 1, 'LexGo': 1, 'LexRust': 1, 'LexScala': 1, 'LexOCaml': 1, 'LexPowerShell': 1, 'LexAssembly': 1, 'LexRoff': 1, 'LexD': 1, 'LexHaskell': 1, 'LexIDL': 1, 'LexYacc': 1, 'LexC#': 1, 'LexSmalltalk': 1, 'LexObjective-C++': 1, 'GoRust': 4, 'GoScala': 4, 'GoOCaml': 2, 'GoPowerShell': 5, 'GoAssembly': 2, 'GoRoff': 5, 'GoD': 1, 'GoHaskell': 1, 'GoIDL': 1, 'GoYacc': 2, 'GoC#': 3, 'GoSmalltalk': 1, 'GoObjective-C++': 3, 'GoTcl': 1, 'GoDIGITAL Command Language': 1, 'GoSQLPL': 1, 'GoTSQL': 1, 'GoCMake': 2, 'GoRuby': 9, 'GoGLSL': 1, 'GoTypeScript': 4, 'GoAppleScript': 1, 'GoCoffeeScript': 2, 'GoHCL': 2, 'GoClojure': 1, 'GoPHP': 4, 'GoPostScript': 3, 'GoDart': 1, 'GoXSLT': 2, 'GoEmacs Lisp': 1, 'GoLua': 3, 'Gosed': 1, 'GoElm': 1, 'GoPascal': 2, 'GoAutoHotkey': 1, 'GoNSIS': 1, 'GoActionScript': 1, 'GoApacheConf': 1, 'GoSmarty': 1, 'GoPLSQL': 1, 'GoPuppet': 1, 'GoTerra': 1, 'RustScala': 3, 'RustOCaml': 1, 'RustPowerShell': 2, 'RustAssembly': 1, 'RustRoff': 2, 'RustD': 1, 'RustHaskell': 1, 'RustIDL': 1, 'RustYacc': 2, 'RustC#': 1, 'RustSmalltalk': 1, 'RustObjective-C++': 3, 'RustCMake': 1, 'RustRuby': 3, 'RustTypeScript': 1, 'RustCoffeeScript': 1, 'RustClojure': 1, 'RustPostScript': 1, 'RustDart': 1, 'RustXSLT': 1, 'RustEmacs Lisp': 1, 'RustLua': 2, 'Rustsed': 1, 'RustElm': 1, 'ScalaOCaml': 1, 'ScalaPowerShell': 3, 'ScalaAssembly': 1, 'ScalaRoff': 3, 'ScalaD': 1, 'ScalaHaskell': 1, 'ScalaIDL': 1, 'ScalaYacc': 1, 'ScalaC#': 1, 'ScalaSmalltalk': 1, 'ScalaObjective-C++': 3, 'ScalaRuby': 3, 'ScalaTypeScript': 2, 'ScalaClojure': 1, 'ScalaPHP': 1, 'ScalaPostScript': 2, 'ScalaDart': 1, 'ScalaXSLT': 2, 'ScalaEmacs Lisp': 1, 'ScalaLua': 2, 'Scalased': 1, 'ScalaElm': 1, 'ScalaPascal': 1, 'ScalaAutoHotkey': 1, 'ScalaNSIS': 1, 'ScalaActionScript': 1, 'ScalaApacheConf': 1, 'ScalaSmarty': 1, 'OCamlPowerShell': 1, 'OCamlAssembly': 1, 'OCamlRoff': 1, 'OCamlD': 1, 'OCamlHaskell': 1, 'OCamlIDL': 1, 'OCamlYacc': 1, 'OCamlC#': 1, 'OCamlSmalltalk': 1, 'OCamlObjective-C++': 1, 'OCamlRuby': 1, 'OCamlTypeScript': 1, 'OCamlAppleScript': 1, 'PowerShellAssembly': 2, 'PowerShellRoff': 5, 'PowerShellD': 1, 'PowerShellHaskell': 1, 'PowerShellIDL': 1, 'PowerShellYacc': 1, 'PowerShellC#': 3, 'PowerShellSmalltalk': 1, 'PowerShellObjective-C++': 4, 'PowerShellTcl': 1, 'PowerShellDIGITAL Command Language': 2, 'PowerShellSQLPL': 1, 'PowerShellTSQL': 1, 'PowerShellCMake': 2, 'PowerShellRuby': 4, 'PowerShellGLSL': 1, 'PowerShellTypeScript': 4, 'PowerShellCoffeeScript': 1, 'PowerShellHCL': 1, 'PowerShellClojure': 2, 'PowerShellPHP': 1, 'PowerShellPostScript': 1, 'PowerShellDart': 3, 'PowerShellVisual Basic': 1, 'PowerShellXSLT': 3, 'PowerShell1C Enterprise': 1, 'PowerShellOpenEdge ABL': 1, 'PowerShellASP': 1, 'PowerShellLua': 1, 'PowerShellsed': 1, 'PowerShellElm': 1, 'PowerShellPascal': 1, 'PowerShellAutoHotkey': 1, 'PowerShellNSIS': 1, 'PowerShellActionScript': 1, 'PowerShellApacheConf': 1, 'PowerShellSmarty': 1, 'AssemblyRoff': 2, 'AssemblyD': 1, 'AssemblyHaskell': 2, 'AssemblyIDL': 2, 'AssemblyYacc': 1, 'AssemblyC#': 2, 'AssemblySmalltalk': 1, 'AssemblyObjective-C++': 2, 'AssemblyTcl': 1, 'AssemblyDIGITAL Command Language': 1, 'AssemblySQLPL': 1, 'AssemblyTSQL': 1, 'AssemblyCMake': 1, 'AssemblyRuby': 2, 'AssemblyGLSL': 1, 'AssemblyClojure': 1, 'RoffD': 1, 'RoffHaskell': 1, 'RoffIDL': 1, 'RoffYacc': 1, 'RoffC#': 4, 'RoffSmalltalk': 1, 'RoffObjective-C++': 4, 'RoffTcl': 1, 'RoffDIGITAL Command Language': 3, 'RoffSQLPL': 1, 'RoffTSQL': 1, 'RoffCMake': 3, 'RoffRuby': 5, 'RoffGLSL': 2, 'RoffTypeScript': 4, 'RoffCoffeeScript': 2, 'RoffClojure': 2, 'RoffPHP': 2, 'RoffPostScript': 2, 'RoffDart': 2, 'RoffVisual Basic': 1, 'RoffXSLT': 3, 'Roff1C Enterprise': 1, 'RoffOpenEdge ABL': 1, 'RoffASP': 1, 'RoffLua': 1, 'Roffsed': 2, 'RoffElm': 1, 'RoffNim': 1, 'RoffM4': 1, 'RoffRagel': 1, 'RoffPascal': 1, 'RoffAutoHotkey': 1, 'RoffNSIS': 1, 'RoffActionScript': 1, 'RoffApacheConf': 1, 'RoffSmarty': 1, 'DHaskell': 1, 'DIDL': 1, 'DYacc': 1, 'DC#': 1, 'DSmalltalk': 1, 'DObjective-C++': 1, 'HaskellIDL': 2, 'HaskellYacc': 1, 'HaskellC#': 1, 'HaskellSmalltalk': 1, 'HaskellObjective-C++': 2, 'HaskellRuby': 1, 'HaskellClojure': 1, 'IDLYacc': 1, 'IDLC#': 1, 'IDLSmalltalk': 1, 'IDLObjective-C++': 2, 'IDLRuby': 1, 'IDLClojure': 1, 'YaccC#': 1, 'YaccSmalltalk': 1, 'YaccObjective-C++': 1, 'YaccCMake': 1, 'YaccLua': 1, 'C#Smalltalk': 1, 'C#Objective-C++': 2, 'C#Tcl': 1, 'C#DIGITAL Command Language': 3, 'C#SQLPL': 1, 'C#TSQL': 1, 'C#CMake': 3, 'C#Ruby': 4, 'C#GLSL': 2, 'C#TypeScript': 3, 'C#AppleScript': 1, 'C#CoffeeScript': 3, 'C#Protocol Buffer': 1, 'C#Clojure': 1, 'C#Dart': 1, 'C#Visual Basic': 1, 'C#XSLT': 1, 'C#1C Enterprise': 1, 'C#OpenEdge ABL': 1, 'C#ASP': 1, 'C#sed': 1, 'C#Nim': 1, 'C#M4': 1, 'C#Ragel': 1, 'SmalltalkObjective-C++': 1, 'Objective-C++DIGITAL Command Language': 1, 'Objective-C++CMake': 1, 'Objective-C++Ruby': 4, 'Objective-C++TypeScript': 3, 'Objective-C++CoffeeScript': 2, 'Objective-C++Clojure': 3, 'Objective-C++PHP': 1, 'Objective-C++PostScript': 1, 'Objective-C++Dart': 2, 'Objective-C++Visual Basic': 1, 'Objective-C++XSLT': 3, 'Objective-C++1C Enterprise': 1, 'Objective-C++OpenEdge ABL': 1, 'Objective-C++ASP': 1, 'Objective-C++Lua': 1, 'Objective-C++sed': 1, 'Objective-C++Elm': 1, 'Objective-C++Pascal': 1, 'Objective-C++AutoHotkey': 1, 'Objective-C++NSIS': 1, 'Objective-C++ActionScript': 1, 'Objective-C++ApacheConf': 1, 'Objective-C++Smarty': 1, 'TclDIGITAL Command Language': 1, 'TclSQLPL': 1, 'TclTSQL': 1, 'TclCMake': 1, 'TclRuby': 1, 'TclGLSL': 1, 'DIGITAL Command LanguageSQLPL': 1, 'DIGITAL Command LanguageTSQL': 1, 'DIGITAL Command LanguageCMake': 3, 'DIGITAL Command LanguageRuby': 2, 'DIGITAL Command LanguageGLSL': 2, 'DIGITAL Command LanguageTypeScript': 1, 'DIGITAL Command LanguageCoffeeScript': 1, 'DIGITAL Command LanguageClojure': 1, 'DIGITAL Command LanguageDart': 1, 'DIGITAL Command LanguageVisual Basic': 1, 'DIGITAL Command LanguageXSLT': 1, 'DIGITAL Command Language1C Enterprise': 1, 'DIGITAL Command LanguageOpenEdge ABL': 1, 'DIGITAL Command LanguageASP': 1, 'DIGITAL Command Languagesed': 1, 'DIGITAL Command LanguageNim': 1, 'DIGITAL Command LanguageM4': 1, 'DIGITAL Command LanguageRagel': 1, 'SQLPLTSQL': 1, 'SQLPLCMake': 1, 'SQLPLRuby': 1, 'SQLPLGLSL': 1, 'TSQLCMake': 1, 'TSQLRuby': 1, 'TSQLGLSL': 1, 'CMakeRuby': 2, 'CMakeGLSL': 2, 'CMakeTypeScript': 1, 'CMakeCoffeeScript': 1, 'CMakeClojure': 1, 'CMakeDart': 1, 'CMakeVisual Basic': 1, 'CMakeXSLT': 1, 'CMake1C Enterprise': 1, 'CMakeOpenEdge ABL': 1, 'CMakeASP': 1, 'CMakeLua': 1, 'CMakesed': 1, 'CMakeNim': 1, 'CMakeM4': 1, 'CMakeRagel': 1, 'RubyGLSL': 2, 'RubyTypeScript': 8, 'RubyAppleScript': 1, 'RubyCoffeeScript': 4, 'RubyProtocol Buffer': 1, 'RubyHCL': 2, 'RubyClojure': 2, 'RubyPHP': 3, 'RubyPostScript': 3, 'RubyDart': 2, 'RubyXSLT': 2, 'RubyEmacs Lisp': 1, 'RubyLua': 2, 'Rubysed': 2, 'RubyElm': 1, 'RubyNim': 1, 'RubyM4': 1, 'RubyRagel': 1, 'RubyPascal': 2, 'RubyAutoHotkey': 1, 'RubyNSIS': 1, 'RubyActionScript': 1, 'RubyApacheConf': 1, 'RubySmarty': 1, 'RubyPLSQL': 1, 'RubyPuppet': 1, 'RubyTerra': 1, 'GLSLsed': 1, 'GLSLNim': 1, 'GLSLM4': 1, 'GLSLRagel': 1, 'TypeScriptAppleScript': 2, 'TypeScriptCoffeeScript': 3, 'TypeScriptProtocol Buffer': 1, 'TypeScriptHCL': 1, 'TypeScriptClojure': 2, 'TypeScriptPHP': 2, 'TypeScriptPostScript': 2, 'TypeScriptDart': 3, 'TypeScriptVisual Basic': 1, 'TypeScriptXSLT': 3, 'TypeScript1C Enterprise': 1, 'TypeScriptOpenEdge ABL': 1, 'TypeScriptASP': 1, 'TypeScriptLua': 1, 'TypeScriptsed': 1, 'TypeScriptElm': 1, 'TypeScriptPascal': 1, 'TypeScriptAutoHotkey': 1, 'TypeScriptNSIS': 1, 'TypeScriptActionScript': 1, 'TypeScriptApacheConf': 1, 'TypeScriptSmarty': 1, 'CoffeeScriptProtocol Buffer': 1, 'CoffeeScriptClojure': 1, 'CoffeeScriptPHP': 1, 'CoffeeScriptPostScript': 1, 'CoffeeScriptDart': 1, 'CoffeeScriptVisual Basic': 1, 'CoffeeScriptXSLT': 1, 'CoffeeScript1C Enterprise': 1, 'CoffeeScriptOpenEdge ABL': 1, 'CoffeeScriptASP': 1, 'HCLPascal': 1, 'HCLPLSQL': 1, 'HCLPuppet': 1, 'ClojureDart': 2, 'ClojureVisual Basic': 1, 'ClojureXSLT': 2, 'Clojure1C Enterprise': 1, 'ClojureOpenEdge ABL': 1, 'ClojureASP': 1, 'Clojuresed': 1, 'ClojureElm': 1, 'PHPPostScript': 2, 'PHPXSLT': 1, 'PHPLua': 1, 'PHPPascal': 1, 'PHPAutoHotkey': 1, 'PHPNSIS': 1, 'PHPActionScript': 1, 'PHPApacheConf': 1, 'PHPSmarty': 1, 'PHPTerra': 1, 'PostScriptXSLT': 1, 'PostScriptEmacs Lisp': 1, 'PostScriptLua': 2, 'PostScriptPascal': 1, 'PostScriptAutoHotkey': 1, 'PostScriptNSIS': 1, 'PostScriptActionScript': 1, 'PostScriptApacheConf': 1, 'PostScriptSmarty': 1, 'DartVisual Basic': 1, 'DartXSLT': 2, 'Dart1C Enterprise': 1, 'DartOpenEdge ABL': 1, 'DartASP': 1, 'Dartsed': 1, 'DartElm': 1, 'Visual BasicXSLT': 1, 'Visual Basic1C Enterprise': 1, 'Visual BasicOpenEdge ABL': 1, 'Visual BasicASP': 1, 'XSLT1C Enterprise': 1, 'XSLTOpenEdge ABL': 1, 'XSLTASP': 1, 'XSLTLua': 1, 'XSLTsed': 1, 'XSLTElm': 1, 'XSLTPascal': 1, 'XSLTAutoHotkey': 1, 'XSLTNSIS': 1, 'XSLTActionScript': 1, 'XSLTApacheConf': 1, 'XSLTSmarty': 1, '1C EnterpriseOpenEdge ABL': 1, '1C EnterpriseASP': 1, 'OpenEdge ABLASP': 1, 'Emacs LispLua': 1, 'LuaPascal': 1, 'LuaAutoHotkey': 1, 'LuaNSIS': 1, 'LuaActionScript': 1, 'LuaApacheConf': 1, 'LuaSmarty': 1, 'sedElm': 1, 'sedNim': 1, 'sedM4': 1, 'sedRagel': 1, 'NimM4': 1, 'NimRagel': 1, 'M4Ragel': 1, 'PascalAutoHotkey': 1, 'PascalNSIS': 1, 'PascalActionScript': 1, 'PascalApacheConf': 1, 'PascalSmarty': 1, 'PascalPLSQL': 1, 'PascalPuppet': 1, 'AutoHotkeyNSIS': 1, 'AutoHotkeyActionScript': 1, 'AutoHotkeyApacheConf': 1, 'AutoHotkeySmarty': 1, 'NSISActionScript': 1, 'NSISApacheConf': 1, 'NSISSmarty': 1, 'ActionScriptApacheConf': 1, 'ActionScriptSmarty': 1, 'ApacheConfSmarty': 1, 'PLSQLPuppet': 1}


    for i in popdict.keys():
        if popdict[i] == max(popdict.values()):
            mode = i


    # Adding edges between langguages and repos
    for lang1 in langs_ids:
        # lang1name = sqlconn.run('SELECT name FROM language WHERE id=%d;' %(lang1[0]))
        for lang2 in langs_ids[langs_ids.index(lang1) + 1:]:
            if (lang1[0] != lang2[0]):
                # langpop = sqlconn.run('SELECT COUNT(repoid) FROM contains WHERE repoid=%d AND (langid=%d OR langid=%d);')
                try:
                    langpop = lang_dict[lang1[1] + lang2[1]]
                    if (langpop > mode):
                        tmp += '  edge [\n    source "' + lang1[1] +'"\n    target "' + lang2[1] +'"\n  ]\n'
                except:
                    pass

    # sqlconn.connection.close()
    tmp += ']'
    filename = 'data/devs_langs_onemode.gml'
    with open(filename, 'w') as f:
        f.write(tmp)

if __name__ == '__main__':
    # scrape_devs()
    # scrape_repos()
    # reposLangsToMysql()
    # devsLangsToMysql()
    repoLangToGml()
    devLangToGml()
    # repoLangOneModeToGml()
    # devLangOneModeToGml()