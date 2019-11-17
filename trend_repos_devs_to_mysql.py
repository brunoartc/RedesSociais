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
    # mode = 0
    '''

    sqlconn.connection.close()
    popdict = {3: 40, 2: 162, 1: 1268, 0: 3746, 6: 6, 4: 14, 11: 2, 5: 7, 8: 3, 9: 2, 12: 2, 7: 1}
    lang_dict = {'Jupyter NotebookPython': 3, 'Jupyter NotebookJavaScript': 2, 'Jupyter NotebookC++': 1, 'Jupyter NotebookShell': 3, 'Jupyter NotebookMATLAB': 1, 'Jupyter NotebookHTML': 2, 'Jupyter NotebookJava': 1, 'Jupyter NotebookCSS': 1, 'Jupyter NotebookDockerfile': 2, 'Jupyter NotebookMakefile': 1, 'Jupyter NotebookRuby': 1, 'Jupyter NotebookPHP': 1, 'Jupyter NotebookASP': 1, 'Jupyter NotebookXSLT': 1, 'PythonJavaScript': 6, 'PythonC++': 4, 'PythonShell': 11, 'PythonMATLAB': 2, 'PythonHTML': 6, 'PythonJava': 3, 'PythonCSS': 5, 'PythonDockerfile': 6, 'PythonGo': 3, 'PythonMakefile': 8, 'PythonSmarty': 1, 'PythonTypeScript': 2, 'PythonInno Setup': 1, 'PythonBatchfile': 3, 'PythonPowerShell': 2, 'PythonGroovy': 1, 'PythonRuby': 3, 'PythonObjective-C': 2, 'PythonObjective-C++': 2, 'PythonClojure': 1, 'PythonPerl 6': 1, 'PythonPHP': 3, 'PythonVisual Basic': 1, 'PythonPerl': 3, 'PythonC': 3, 'PythonF#': 1, 'PythonCoffeeScript': 1, 'PythonRust': 2, 'PythonC#': 2, 'PythonR': 2, 'PythonRoff': 3, 'PythonShaderLab': 1, 'PythonSwift': 2, 'PythonLua': 1, 'PythonHLSL': 1, 'PythonHack': 1, 'PythonLLVM': 1, 'PythonAssembly': 1, 'PythonCMake': 1, 'PythonCuda': 1, 'PythonOCaml': 1, 'PythonAwk': 1, 'PythonM4': 1, 'PythonTeX': 1, 'PythonEmacs Lisp': 1, 'PythonSmalltalk': 1, 'PythonPawn': 1, 'PythonCool': 1, 'PythonVim script': 1, 'PythonFortran': 1, 'PythonMathematica': 1, 'PythonM': 1, 'PythonSuperCollider': 1, 'PythonCommon Lisp': 1, 'PythonAppleScript': 1, 'PythonMercury': 1, 'PythonPascal': 1, 'PythonForth': 1, 'PythonRenderScript': 1, 'PythonDTrace': 1, 'PythonLogos': 1, 'PythonASP': 1, 'PythonXSLT': 1, 'PythonKotlin': 1, 'PythonProlog': 1, 'JavaScriptC++': 3, 'JavaScriptShell': 9, 'JavaScriptMATLAB': 2, 'JavaScriptHTML': 12, 'JavaScriptJava': 3, 'JavaScriptCSS': 12, 'JavaScriptDockerfile': 5, 'JavaScriptGo': 3, 'JavaScriptMakefile': 5, 'JavaScriptTypeScript': 4, 'JavaScriptInno Setup': 1, 'JavaScriptBatchfile': 4, 'JavaScriptPowerShell': 2, 'JavaScriptGroovy': 1, 'JavaScriptRuby': 3, 'JavaScriptObjective-C': 2, 'JavaScriptObjective-C++': 2, 'JavaScriptClojure': 1, 'JavaScriptPerl 6': 1, 'JavaScriptPHP': 3, 'JavaScriptVisual Basic': 1, 'JavaScriptPerl': 2, 'JavaScriptC': 2, 'JavaScriptF#': 1, 'JavaScriptCoffeeScript': 1, 'JavaScriptRust': 2, 'JavaScriptC#': 2, 'JavaScriptR': 2, 'JavaScriptRoff': 2, 'JavaScriptShaderLab': 1, 'JavaScriptSwift': 2, 'JavaScriptLua': 1, 'JavaScriptHLSL': 1, 'JavaScriptHack': 1, 'JavaScriptLLVM': 1, 'JavaScriptAssembly': 1, 'JavaScriptCMake': 1, 'JavaScriptCuda': 1, 'JavaScriptOCaml': 1, 'JavaScriptAwk': 1, 'JavaScriptM4': 1, 'JavaScriptTeX': 1, 'JavaScriptEmacs Lisp': 1, 'JavaScriptSmalltalk': 1, 'JavaScriptPawn': 1, 'JavaScriptCool': 1, 'JavaScriptVim script': 1, 'JavaScriptFortran': 1, 'JavaScriptMathematica': 1, 'JavaScriptM': 1, 'JavaScriptSuperCollider': 1, 'JavaScriptCommon Lisp': 1, 'JavaScriptAppleScript': 1, 'JavaScriptMercury': 1, 'JavaScriptPascal': 1, 'JavaScriptForth': 1, 'JavaScriptRenderScript': 1, 'JavaScriptDTrace': 1, 'JavaScriptLogos': 1, 'JavaScriptVue': 1, 'JavaScriptPLpgSQL': 1, 'JavaScriptTSQL': 1, 'JavaScriptASP': 1, 'JavaScriptXSLT': 1, 'C++Shell': 4, 'C++MATLAB': 2, 'C++HTML': 3, 'C++Java': 3, 'C++CSS': 3, 'C++Dockerfile': 3, 'C++Go': 2, 'C++Makefile': 3, 'C++TypeScript': 1, 'C++Inno Setup': 1, 'C++Batchfile': 2, 'C++PowerShell': 1, 'C++Groovy': 1, 'C++Ruby': 1, 'C++Objective-C': 2, 'C++Objective-C++': 2, 'C++Clojure': 1, 'C++Perl 6': 1, 'C++PHP': 2, 'C++Visual Basic': 1, 'C++Perl': 2, 'C++C': 3, 'C++F#': 1, 'C++CoffeeScript': 1, 'C++Rust': 2, 'C++C#': 2, 'C++R': 2, 'C++Roff': 2, 'C++ShaderLab': 1, 'C++Swift': 2, 'C++Lua': 1, 'C++HLSL': 1, 'C++Hack': 1, 'C++LLVM': 1, 'C++Assembly': 1, 'C++CMake': 1, 'C++Cuda': 1, 'C++OCaml': 1, 'C++Awk': 1, 'C++M4': 1, 'C++TeX': 1, 'C++Emacs Lisp': 1, 'C++Smalltalk': 1, 'C++Pawn': 1, 'C++Cool': 1, 'C++Vim script': 1, 'C++Fortran': 1, 'C++Mathematica': 1, 'C++M': 1, 'C++SuperCollider': 1, 'C++Common Lisp': 1, 'C++AppleScript': 1, 'C++Mercury': 1, 'C++Pascal': 1, 'C++Forth': 1, 'C++RenderScript': 1, 'C++DTrace': 1, 'C++Logos': 1, 'C++Kotlin': 1, 'C++Prolog': 1, 'ShellMATLAB': 2, 'ShellHTML': 8, 'ShellJava': 4, 'ShellCSS': 8, 'ShellDockerfile': 7, 'ShellGo': 4, 'ShellMakefile': 9, 'ShellSmarty': 1, 'ShellTypeScript': 3, 'ShellInno Setup': 1, 'ShellBatchfile': 4, 'ShellPowerShell': 2, 'ShellGroovy': 1, 'ShellRuby': 4, 'ShellObjective-C': 2, 'ShellObjective-C++': 2, 'ShellClojure': 1, 'ShellPerl 6': 1, 'ShellPHP': 3, 'ShellVisual Basic': 1, 'ShellPerl': 3, 'ShellC': 3, 'ShellF#': 1, 'ShellCoffeeScript': 1, 'ShellRust': 2, 'ShellC#': 2, 'ShellR': 2, 'ShellRoff': 3, 'ShellShaderLab': 1, 'ShellSwift': 2, 'ShellLua': 1, 'ShellHLSL': 1, 'ShellHack': 1, 'ShellLLVM': 1, 'ShellAssembly': 1, 'ShellCMake': 1, 'ShellCuda': 1, 'ShellOCaml': 1, 'ShellAwk': 1, 'ShellM4': 1, 'ShellTeX': 1, 'ShellEmacs Lisp': 1, 'ShellSmalltalk': 1, 'ShellPawn': 1, 'ShellCool': 1, 'ShellVim script': 1, 'ShellFortran': 1, 'ShellMathematica': 1, 'ShellM': 1, 'ShellSuperCollider': 1, 'ShellCommon Lisp': 1, 'ShellAppleScript': 1, 'ShellMercury': 1, 'ShellPascal': 1, 'ShellForth': 1, 'ShellRenderScript': 1, 'ShellDTrace': 1, 'ShellLogos': 1, 'ShellASP': 1, 'ShellXSLT': 1, 'ShellKotlin': 1, 'ShellProlog': 1, 'MATLABHTML': 2, 'MATLABJava': 1, 'MATLABCSS': 2, 'MATLABDockerfile': 2, 'MATLABGo': 1, 'MATLABMakefile': 1, 'MATLABBatchfile': 1, 'MATLABObjective-C': 1, 'MATLABObjective-C++': 1, 'MATLABPHP': 1, 'MATLABPerl': 1, 'MATLABC': 1, 'MATLABRust': 1, 'MATLABC#': 1, 'MATLABR': 1, 'MATLABRoff': 1, 'MATLABSwift': 1, 'MATLABLLVM': 1, 'MATLABAssembly': 1, 'MATLABCMake': 1, 'MATLABCuda': 1, 'MATLABOCaml': 1, 'MATLABAwk': 1, 'MATLABM4': 1, 'MATLABTeX': 1, 'MATLABEmacs Lisp': 1, 'MATLABSmalltalk': 1, 'MATLABPawn': 1, 'MATLABCool': 1, 'MATLABVim script': 1, 'MATLABFortran': 1, 'MATLABMathematica': 1, 'MATLABM': 1, 'MATLABSuperCollider': 1, 'MATLABCommon Lisp': 1, 'MATLABAppleScript': 1, 'MATLABMercury': 1, 'MATLABPascal': 1, 'MATLABForth': 1, 'MATLABRenderScript': 1, 'MATLABDTrace': 1, 'MATLABLogos': 1, 'HTMLJava': 3, 'HTMLCSS': 11, 'HTMLDockerfile': 6, 'HTMLGo': 3, 'HTMLMakefile': 6, 'HTMLTypeScript': 4, 'HTMLInno Setup': 1, 'HTMLBatchfile': 5, 'HTMLPowerShell': 2, 'HTMLGroovy': 1, 'HTMLRuby': 2, 'HTMLObjective-C': 2, 'HTMLObjective-C++': 2, 'HTMLClojure': 1, 'HTMLPerl 6': 1, 'HTMLPHP': 3, 'HTMLVisual Basic': 1, 'HTMLPerl': 2, 'HTMLC': 3, 'HTMLF#': 1, 'HTMLCoffeeScript': 1, 'HTMLRust': 2, 'HTMLC#': 2, 'HTMLR': 2, 'HTMLRoff': 2, 'HTMLShaderLab': 1, 'HTMLSwift': 2, 'HTMLLua': 1, 'HTMLHLSL': 1, 'HTMLHack': 1, 'HTMLLLVM': 1, 'HTMLAssembly': 2, 'HTMLCMake': 1, 'HTMLCuda': 1, 'HTMLOCaml': 1, 'HTMLAwk': 1, 'HTMLM4': 1, 'HTMLTeX': 1, 'HTMLEmacs Lisp': 1, 'HTMLSmalltalk': 1, 'HTMLPawn': 1, 'HTMLCool': 1, 'HTMLVim script': 1, 'HTMLFortran': 1, 'HTMLMathematica': 1, 'HTMLM': 1, 'HTMLSuperCollider': 1, 'HTMLCommon Lisp': 1, 'HTMLAppleScript': 1, 'HTMLMercury': 1, 'HTMLPascal': 1, 'HTMLForth': 1, 'HTMLRenderScript': 1, 'HTMLDTrace': 1, 'HTMLLogos': 1, 'HTMLV': 1, 'HTMLVue': 1, 'HTMLPLpgSQL': 1, 'HTMLTSQL': 1, 'HTMLASP': 1, 'HTMLXSLT': 1, 'JavaCSS': 3, 'JavaDockerfile': 2, 'JavaGo': 1, 'JavaMakefile': 2, 'JavaTypeScript': 1, 'JavaInno Setup': 1, 'JavaBatchfile': 1, 'JavaPowerShell': 1, 'JavaGroovy': 1, 'JavaRuby': 1, 'JavaObjective-C': 1, 'JavaObjective-C++': 1, 'JavaClojure': 1, 'JavaPerl 6': 1, 'JavaPHP': 1, 'JavaVisual Basic': 1, 'JavaPerl': 1, 'JavaC': 2, 'JavaF#': 1, 'JavaCoffeeScript': 1, 'JavaRust': 1, 'JavaC#': 1, 'JavaR': 1, 'JavaRoff': 1, 'JavaShaderLab': 1, 'JavaSwift': 1, 'JavaLua': 1, 'JavaHLSL': 1, 'JavaHack': 1, 'JavaVue': 1, 'JavaPLpgSQL': 1, 'JavaTSQL': 1, 'JavaKotlin': 1, 'JavaProlog': 1, 'CSSDockerfile': 5, 'CSSGo': 3, 'CSSMakefile': 5, 'CSSTypeScript': 4, 'CSSInno Setup': 1, 'CSSBatchfile': 4, 'CSSPowerShell': 2, 'CSSGroovy': 1, 'CSSRuby': 2, 'CSSObjective-C': 2, 'CSSObjective-C++': 2, 'CSSClojure': 1, 'CSSPerl 6': 1, 'CSSPHP': 2, 'CSSVisual Basic': 1, 'CSSPerl': 2, 'CSSC': 2, 'CSSF#': 1, 'CSSCoffeeScript': 1, 'CSSRust': 2, 'CSSC#': 2, 'CSSR': 2, 'CSSRoff': 2, 'CSSShaderLab': 1, 'CSSSwift': 2, 'CSSLua': 1, 'CSSHLSL': 1, 'CSSHack': 1, 'CSSLLVM': 1, 'CSSAssembly': 1, 'CSSCMake': 1, 'CSSCuda': 1, 'CSSOCaml': 1, 'CSSAwk': 1, 'CSSM4': 1, 'CSSTeX': 1, 'CSSEmacs Lisp': 1, 'CSSSmalltalk': 1, 'CSSPawn': 1, 'CSSCool': 1, 'CSSVim script': 1, 'CSSFortran': 1, 'CSSMathematica': 1, 'CSSM': 1, 'CSSSuperCollider': 1, 'CSSCommon Lisp': 1, 'CSSAppleScript': 1, 'CSSMercury': 1, 'CSSPascal': 1, 'CSSForth': 1, 'CSSRenderScript': 1, 'CSSDTrace': 1, 'CSSLogos': 1, 'CSSVue': 1, 'CSSPLpgSQL': 1, 'CSSTSQL': 1, 'DockerfileGo': 3, 'DockerfileMakefile': 6, 'DockerfileSmarty': 1, 'DockerfileTypeScript': 3, 'DockerfileInno Setup': 1, 'DockerfileBatchfile': 4, 'DockerfilePowerShell': 1, 'DockerfileGroovy': 1, 'DockerfileRuby': 1, 'DockerfileObjective-C': 2, 'DockerfileObjective-C++': 2, 'DockerfileClojure': 1, 'DockerfilePerl 6': 1, 'DockerfilePHP': 2, 'DockerfileVisual Basic': 1, 'DockerfilePerl': 2, 'DockerfileC': 3, 'DockerfileF#': 1, 'DockerfileCoffeeScript': 1, 'DockerfileRust': 2, 'DockerfileC#': 2, 'DockerfileR': 2, 'DockerfileRoff': 2, 'DockerfileShaderLab': 1, 'DockerfileSwift': 2, 'DockerfileLua': 1, 'DockerfileHLSL': 1, 'DockerfileHack': 1, 'DockerfileLLVM': 1, 'DockerfileAssembly': 2, 'DockerfileCMake': 1, 'DockerfileCuda': 1, 'DockerfileOCaml': 1, 'DockerfileAwk': 1, 'DockerfileM4': 1, 'DockerfileTeX': 1, 'DockerfileEmacs Lisp': 1, 'DockerfileSmalltalk': 1, 'DockerfilePawn': 1, 'DockerfileCool': 1, 'DockerfileVim script': 1, 'DockerfileFortran': 1, 'DockerfileMathematica': 1, 'DockerfileM': 1, 'DockerfileSuperCollider': 1, 'DockerfileCommon Lisp': 1, 'DockerfileAppleScript': 1, 'DockerfileMercury': 1, 'DockerfilePascal': 1, 'DockerfileForth': 1, 'DockerfileRenderScript': 1, 'DockerfileDTrace': 1, 'DockerfileLogos': 1, 'DockerfileV': 1, 'GoMakefile': 4, 'GoSmarty': 1, 'GoTypeScript': 1, 'GoInno Setup': 1, 'GoBatchfile': 3, 'GoPowerShell': 1, 'GoGroovy': 1, 'GoRuby': 1, 'GoObjective-C': 2, 'GoObjective-C++': 2, 'GoClojure': 1, 'GoPerl 6': 1, 'GoPHP': 2, 'GoVisual Basic': 1, 'GoPerl': 2, 'GoC': 2, 'GoF#': 1, 'GoCoffeeScript': 1, 'GoRust': 2, 'GoC#': 2, 'GoR': 2, 'GoRoff': 2, 'GoShaderLab': 1, 'GoSwift': 2, 'GoLua': 1, 'GoHLSL': 1, 'GoHack': 1, 'GoLLVM': 1, 'GoAssembly': 1, 'GoCMake': 1, 'GoCuda': 1, 'GoOCaml': 1, 'GoAwk': 1, 'GoM4': 1, 'GoTeX': 1, 'GoEmacs Lisp': 1, 'GoSmalltalk': 1, 'GoPawn': 1, 'GoCool': 1, 'GoVim script': 1, 'GoFortran': 1, 'GoMathematica': 1, 'GoM': 1, 'GoSuperCollider': 1, 'GoCommon Lisp': 1, 'GoAppleScript': 1, 'GoMercury': 1, 'GoPascal': 1, 'GoForth': 1, 'GoRenderScript': 1, 'GoDTrace': 1, 'GoLogos': 1, 'MakefileSmarty': 1, 'MakefileTypeScript': 2, 'MakefileInno Setup': 1, 'MakefileBatchfile': 5, 'MakefilePowerShell': 2, 'MakefileGroovy': 1, 'MakefileRuby': 2, 'MakefileObjective-C': 2, 'MakefileObjective-C++': 2, 'MakefileClojure': 1, 'MakefilePerl 6': 1, 'MakefilePHP': 2, 'MakefileVisual Basic': 1, 'MakefilePerl': 3, 'MakefileC': 4, 'MakefileF#': 1, 'MakefileCoffeeScript': 1, 'MakefileRust': 2, 'MakefileC#': 2, 'MakefileR': 2, 'MakefileRoff': 3, 'MakefileShaderLab': 1, 'MakefileSwift': 2, 'MakefileLua': 1, 'MakefileHLSL': 1, 'MakefileHack': 1, 'MakefileLLVM': 1, 'MakefileAssembly': 2, 'MakefileCMake': 1, 'MakefileCuda': 1, 'MakefileOCaml': 1, 'MakefileAwk': 1, 'MakefileM4': 1, 'MakefileTeX': 1, 'MakefileEmacs Lisp': 1, 'MakefileSmalltalk': 1, 'MakefilePawn': 1, 'MakefileCool': 1, 'MakefileVim script': 1, 'MakefileFortran': 1, 'MakefileMathematica': 1, 'MakefileM': 1, 'MakefileSuperCollider': 1, 'MakefileCommon Lisp': 1, 'MakefileAppleScript': 1, 'MakefileMercury': 1, 'MakefilePascal': 1, 'MakefileForth': 1, 'MakefileRenderScript': 1, 'MakefileDTrace': 1, 'MakefileLogos': 1, 'MakefileV': 1, 'MakefileKotlin': 1, 'MakefileProlog': 1, 'TypeScriptInno Setup': 1, 'TypeScriptBatchfile': 2, 'TypeScriptPowerShell': 1, 'TypeScriptGroovy': 1, 'TypeScriptRuby': 1, 'TypeScriptObjective-C': 1, 'TypeScriptObjective-C++': 1, 'TypeScriptClojure': 1, 'TypeScriptPerl 6': 1, 'TypeScriptPHP': 1, 'TypeScriptVisual Basic': 1, 'TypeScriptPerl': 1, 'TypeScriptC': 1, 'TypeScriptF#': 1, 'TypeScriptCoffeeScript': 1, 'TypeScriptRust': 1, 'TypeScriptC#': 1, 'TypeScriptR': 1, 'TypeScriptRoff': 1, 'TypeScriptShaderLab': 1, 'TypeScriptSwift': 1, 'TypeScriptLua': 1, 'TypeScriptHLSL': 1, 'TypeScriptHack': 1, 'Inno SetupBatchfile': 1, 'Inno SetupPowerShell': 1, 'Inno SetupGroovy': 1, 'Inno SetupRuby': 1, 'Inno SetupObjective-C': 1, 'Inno SetupObjective-C++': 1, 'Inno SetupClojure': 1, 'Inno SetupPerl 6': 1, 'Inno SetupPHP': 1, 'Inno SetupVisual Basic': 1, 'Inno SetupPerl': 1, 'Inno SetupC': 1, 'Inno SetupF#': 1, 'Inno SetupCoffeeScript': 1, 'Inno SetupRust': 1, 'Inno SetupC#': 1, 'Inno SetupR': 1, 'Inno SetupRoff': 1, 'Inno SetupShaderLab': 1, 'Inno SetupSwift': 1, 'Inno SetupLua': 1, 'Inno SetupHLSL': 1, 'Inno SetupHack': 1, 'BatchfilePowerShell': 1, 'BatchfileGroovy': 1, 'BatchfileRuby': 1, 'BatchfileObjective-C': 2, 'BatchfileObjective-C++': 2, 'BatchfileClojure': 1, 'BatchfilePerl 6': 1, 'BatchfilePHP': 2, 'BatchfileVisual Basic': 1, 'BatchfilePerl': 2, 'BatchfileC': 3, 'BatchfileF#': 1, 'BatchfileCoffeeScript': 1, 'BatchfileRust': 2, 'BatchfileC#': 2, 'BatchfileR': 2, 'BatchfileRoff': 2, 'BatchfileShaderLab': 1, 'BatchfileSwift': 2, 'BatchfileLua': 1, 'BatchfileHLSL': 1, 'BatchfileHack': 1, 'BatchfileLLVM': 1, 'BatchfileAssembly': 2, 'BatchfileCMake': 1, 'BatchfileCuda': 1, 'BatchfileOCaml': 1, 'BatchfileAwk': 1, 'BatchfileM4': 1, 'BatchfileTeX': 1, 'BatchfileEmacs Lisp': 1, 'BatchfileSmalltalk': 1, 'BatchfilePawn': 1, 'BatchfileCool': 1, 'BatchfileVim script': 1, 'BatchfileFortran': 1, 'BatchfileMathematica': 1, 'BatchfileM': 1, 'BatchfileSuperCollider': 1, 'BatchfileCommon Lisp': 1, 'BatchfileAppleScript': 1, 'BatchfileMercury': 1, 'BatchfilePascal': 1, 'BatchfileForth': 1, 'BatchfileRenderScript': 1, 'BatchfileDTrace': 1, 'BatchfileLogos': 1, 'BatchfileV': 1, 'PowerShellGroovy': 1, 'PowerShellRuby': 1, 'PowerShellObjective-C': 1, 'PowerShellObjective-C++': 1, 'PowerShellClojure': 1, 'PowerShellPerl 6': 1, 'PowerShellPHP': 1, 'PowerShellVisual Basic': 1, 'PowerShellPerl': 1, 'PowerShellC': 1, 'PowerShellF#': 1, 'PowerShellCoffeeScript': 1, 'PowerShellRust': 1, 'PowerShellC#': 1, 'PowerShellR': 1, 'PowerShellRoff': 1, 'PowerShellShaderLab': 1, 'PowerShellSwift': 1, 'PowerShellLua': 1, 'PowerShellHLSL': 1, 'PowerShellHack': 1, 'GroovyRuby': 1, 'GroovyObjective-C': 1, 'GroovyObjective-C++': 1, 'GroovyClojure': 1, 'GroovyPerl 6': 1, 'GroovyPHP': 1, 'GroovyVisual Basic': 1, 'GroovyPerl': 1, 'GroovyC': 1, 'GroovyF#': 1, 'GroovyCoffeeScript': 1, 'GroovyRust': 1, 'GroovyC#': 1, 'GroovyR': 1, 'GroovyRoff': 1, 'GroovyShaderLab': 1, 'GroovySwift': 1, 'GroovyLua': 1, 'GroovyHLSL': 1, 'GroovyHack': 1, 'RubyObjective-C': 1, 'RubyObjective-C++': 1, 'RubyClojure': 1, 'RubyPerl 6': 1, 'RubyPHP': 2, 'RubyVisual Basic': 1, 'RubyPerl': 2, 'RubyC': 1, 'RubyF#': 1, 'RubyCoffeeScript': 1, 'RubyRust': 1, 'RubyC#': 1, 'RubyR': 1, 'RubyRoff': 2, 'RubyShaderLab': 1, 'RubySwift': 1, 'RubyLua': 1, 'RubyHLSL': 1, 'RubyHack': 1, 'RubyASP': 1, 'RubyXSLT': 1, 'Objective-CObjective-C++': 2, 'Objective-CClojure': 1, 'Objective-CPerl 6': 1, 'Objective-CPHP': 2, 'Objective-CVisual Basic': 1, 'Objective-CPerl': 2, 'Objective-CC': 2, 'Objective-CF#': 1, 'Objective-CCoffeeScript': 1, 'Objective-CRust': 2, 'Objective-CC#': 2, 'Objective-CR': 2, 'Objective-CRoff': 2, 'Objective-CShaderLab': 1, 'Objective-CSwift': 2, 'Objective-CLua': 1, 'Objective-CHLSL': 1, 'Objective-CHack': 1, 'Objective-CLLVM': 1, 'Objective-CAssembly': 1, 'Objective-CCMake': 1, 'Objective-CCuda': 1, 'Objective-COCaml': 1, 'Objective-CAwk': 1, 'Objective-CM4': 1, 'Objective-CTeX': 1, 'Objective-CEmacs Lisp': 1, 'Objective-CSmalltalk': 1, 'Objective-CPawn': 1, 'Objective-CCool': 1, 'Objective-CVim script': 1, 'Objective-CFortran': 1, 'Objective-CMathematica': 1, 'Objective-CM': 1, 'Objective-CSuperCollider': 1, 'Objective-CCommon Lisp': 1, 'Objective-CAppleScript': 1, 'Objective-CMercury': 1, 'Objective-CPascal': 1, 'Objective-CForth': 1, 'Objective-CRenderScript': 1, 'Objective-CDTrace': 1, 'Objective-CLogos': 1, 'Objective-C++Clojure': 1, 'Objective-C++Perl 6': 1, 'Objective-C++PHP': 2, 'Objective-C++Visual Basic': 1, 'Objective-C++Perl': 2, 'Objective-C++C': 2, 'Objective-C++F#': 1, 'Objective-C++CoffeeScript': 1, 'Objective-C++Rust': 2, 'Objective-C++C#': 2, 'Objective-C++R': 2, 'Objective-C++Roff': 2, 'Objective-C++ShaderLab': 1, 'Objective-C++Swift': 2, 'Objective-C++Lua': 1, 'Objective-C++HLSL': 1, 'Objective-C++Hack': 1, 'Objective-C++LLVM': 1, 'Objective-C++Assembly': 1, 'Objective-C++CMake': 1, 'Objective-C++Cuda': 1, 'Objective-C++OCaml': 1, 'Objective-C++Awk': 1, 'Objective-C++M4': 1, 'Objective-C++TeX': 1, 'Objective-C++Emacs Lisp': 1, 'Objective-C++Smalltalk': 1, 'Objective-C++Pawn': 1, 'Objective-C++Cool': 1, 'Objective-C++Vim script': 1, 'Objective-C++Fortran': 1, 'Objective-C++Mathematica': 1, 'Objective-C++M': 1, 'Objective-C++SuperCollider': 1, 'Objective-C++Common Lisp': 1, 'Objective-C++AppleScript': 1, 'Objective-C++Mercury': 1, 'Objective-C++Pascal': 1, 'Objective-C++Forth': 1, 'Objective-C++RenderScript': 1, 'Objective-C++DTrace': 1, 'Objective-C++Logos': 1, 'ClojurePerl 6': 1, 'ClojurePHP': 1, 'ClojureVisual Basic': 1, 'ClojurePerl': 1, 'ClojureC': 1, 'ClojureF#': 1, 'ClojureCoffeeScript': 1, 'ClojureRust': 1, 'ClojureC#': 1, 'ClojureR': 1, 'ClojureRoff': 1, 'ClojureShaderLab': 1, 'ClojureSwift': 1, 'ClojureLua': 1, 'ClojureHLSL': 1, 'ClojureHack': 1, 'Perl 6PHP': 1, 'Perl 6Visual Basic': 1, 'Perl 6Perl': 1, 'Perl 6C': 1, 'Perl 6F#': 1, 'Perl 6CoffeeScript': 1, 'Perl 6Rust': 1, 'Perl 6C#': 1, 'Perl 6R': 1, 'Perl 6Roff': 1, 'Perl 6ShaderLab': 1, 'Perl 6Swift': 1, 'Perl 6Lua': 1, 'Perl 6HLSL': 1, 'Perl 6Hack': 1, 'PHPVisual Basic': 1, 'PHPPerl': 2, 'PHPC': 2, 'PHPF#': 1, 'PHPCoffeeScript': 1, 'PHPRust': 2, 'PHPC#': 2, 'PHPR': 2, 'PHPRoff': 2, 'PHPShaderLab': 1, 'PHPSwift': 2, 'PHPLua': 1, 'PHPHLSL': 1, 'PHPHack': 1, 'PHPLLVM': 1, 'PHPAssembly': 1, 'PHPCMake': 1, 'PHPCuda': 1, 'PHPOCaml': 1, 'PHPAwk': 1, 'PHPM4': 1, 'PHPTeX': 1, 'PHPEmacs Lisp': 1, 'PHPSmalltalk': 1, 'PHPPawn': 1, 'PHPCool': 1, 'PHPVim script': 1, 'PHPFortran': 1, 'PHPMathematica': 1, 'PHPM': 1, 'PHPSuperCollider': 1, 'PHPCommon Lisp': 1, 'PHPAppleScript': 1, 'PHPMercury': 1, 'PHPPascal': 1, 'PHPForth': 1, 'PHPRenderScript': 1, 'PHPDTrace': 1, 'PHPLogos': 1, 'PHPASP': 1, 'PHPXSLT': 1, 'Visual BasicPerl': 1, 'Visual BasicC': 1, 'Visual BasicF#': 1, 'Visual BasicCoffeeScript': 1, 'Visual BasicRust': 1, 'Visual BasicC#': 1, 'Visual BasicR': 1, 'Visual BasicRoff': 1, 'Visual BasicShaderLab': 1, 'Visual BasicSwift': 1, 'Visual BasicLua': 1, 'Visual BasicHLSL': 1, 'Visual BasicHack': 1, 'PerlC': 2, 'PerlF#': 1, 'PerlCoffeeScript': 1, 'PerlRust': 2, 'PerlC#': 2, 'PerlR': 2, 'PerlRoff': 3, 'PerlShaderLab': 1, 'PerlSwift': 2, 'PerlLua': 1, 'PerlHLSL': 1, 'PerlHack': 1, 'PerlLLVM': 1, 'PerlAssembly': 1, 'PerlCMake': 1, 'PerlCuda': 1, 'PerlOCaml': 1, 'PerlAwk': 1, 'PerlM4': 1, 'PerlTeX': 1, 'PerlEmacs Lisp': 1, 'PerlSmalltalk': 1, 'PerlPawn': 1, 'PerlCool': 1, 'PerlVim script': 1, 'PerlFortran': 1, 'PerlMathematica': 1, 'PerlM': 1, 'PerlSuperCollider': 1, 'PerlCommon Lisp': 1, 'PerlAppleScript': 1, 'PerlMercury': 1, 'PerlPascal': 1, 'PerlForth': 1, 'PerlRenderScript': 1, 'PerlDTrace': 1, 'PerlLogos': 1, 'CF#': 1, 'CCoffeeScript': 1, 'CRust': 2, 'CC#': 2, 'CR': 2, 'CRoff': 2, 'CShaderLab': 1, 'CSwift': 2, 'CLua': 1, 'CHLSL': 1, 'CHack': 1, 'CLLVM': 1, 'CAssembly': 2, 'CCMake': 1, 'CCuda': 1, 'COCaml': 1, 'CAwk': 1, 'CM4': 1, 'CTeX': 1, 'CEmacs Lisp': 1, 'CSmalltalk': 1, 'CPawn': 1, 'CCool': 1, 'CVim script': 1, 'CFortran': 1, 'CMathematica': 1, 'CM': 1, 'CSuperCollider': 1, 'CCommon Lisp': 1, 'CAppleScript': 1, 'CMercury': 1, 'CPascal': 1, 'CForth': 1, 'CRenderScript': 1, 'CDTrace': 1, 'CLogos': 1, 'CV': 1, 'CKotlin': 1, 'CProlog': 1, 'F#CoffeeScript': 1, 'F#Rust': 1, 'F#C#': 1, 'F#R': 1, 'F#Roff': 1, 'F#ShaderLab': 1, 'F#Swift': 1, 'F#Lua': 1, 'F#HLSL': 1, 'F#Hack': 1, 'CoffeeScriptRust': 1, 'CoffeeScriptC#': 1, 'CoffeeScriptR': 1, 'CoffeeScriptRoff': 1, 'CoffeeScriptShaderLab': 1, 'CoffeeScriptSwift': 1, 'CoffeeScriptLua': 1, 'CoffeeScriptHLSL': 1, 'CoffeeScriptHack': 1, 'RustC#': 2, 'RustR': 2, 'RustRoff': 2, 'RustShaderLab': 1, 'RustSwift': 2, 'RustLua': 1, 'RustHLSL': 1, 'RustHack': 1, 'RustLLVM': 1, 'RustAssembly': 1, 'RustCMake': 1, 'RustCuda': 1, 'RustOCaml': 1, 'RustAwk': 1, 'RustM4': 1, 'RustTeX': 1, 'RustEmacs Lisp': 1, 'RustSmalltalk': 1, 'RustPawn': 1, 'RustCool': 1, 'RustVim script': 1, 'RustFortran': 1, 'RustMathematica': 1, 'RustM': 1, 'RustSuperCollider': 1, 'RustCommon Lisp': 1, 'RustAppleScript': 1, 'RustMercury': 1, 'RustPascal': 1, 'RustForth': 1, 'RustRenderScript': 1, 'RustDTrace': 1, 'RustLogos': 1, 'C#R': 2, 'C#Roff': 2, 'C#ShaderLab': 1, 'C#Swift': 2, 'C#Lua': 1, 'C#HLSL': 1, 'C#Hack': 1, 'C#LLVM': 1, 'C#Assembly': 1, 'C#CMake': 1, 'C#Cuda': 1, 'C#OCaml': 1, 'C#Awk': 1, 'C#M4': 1, 'C#TeX': 1, 'C#Emacs Lisp': 1, 'C#Smalltalk': 1, 'C#Pawn': 1, 'C#Cool': 1, 'C#Vim script': 1, 'C#Fortran': 1, 'C#Mathematica': 1, 'C#M': 1, 'C#SuperCollider': 1, 'C#Common Lisp': 1, 'C#AppleScript': 1, 'C#Mercury': 1, 'C#Pascal': 1, 'C#Forth': 1, 'C#RenderScript': 1, 'C#DTrace': 1, 'C#Logos': 1, 'RRoff': 2, 'RShaderLab': 1, 'RSwift': 2, 'RLua': 1, 'RHLSL': 1, 'RHack': 1, 'RLLVM': 1, 'RAssembly': 1, 'RCMake': 1, 'RCuda': 1, 'ROCaml': 1, 'RAwk': 1, 'RM4': 1, 'RTeX': 1, 'REmacs Lisp': 1, 'RSmalltalk': 1, 'RPawn': 1, 'RCool': 1, 'RVim script': 1, 'RFortran': 1, 'RMathematica': 1, 'RM': 1, 'RSuperCollider': 1, 'RCommon Lisp': 1, 'RAppleScript': 1, 'RMercury': 1, 'RPascal': 1, 'RForth': 1, 'RRenderScript': 1, 'RDTrace': 1, 'RLogos': 1, 'RoffShaderLab': 1, 'RoffSwift': 2, 'RoffLua': 1, 'RoffHLSL': 1, 'RoffHack': 1, 'RoffLLVM': 1, 'RoffAssembly': 1, 'RoffCMake': 1, 'RoffCuda': 1, 'RoffOCaml': 1, 'RoffAwk': 1, 'RoffM4': 1, 'RoffTeX': 1, 'RoffEmacs Lisp': 1, 'RoffSmalltalk': 1, 'RoffPawn': 1, 'RoffCool': 1, 'RoffVim script': 1, 'RoffFortran': 1, 'RoffMathematica': 1, 'RoffM': 1, 'RoffSuperCollider': 1, 'RoffCommon Lisp': 1, 'RoffAppleScript': 1, 'RoffMercury': 1, 'RoffPascal': 1, 'RoffForth': 1, 'RoffRenderScript': 1, 'RoffDTrace': 1, 'RoffLogos': 1, 'ShaderLabSwift': 1, 'ShaderLabLua': 1, 'ShaderLabHLSL': 1, 'ShaderLabHack': 1, 'SwiftLua': 1, 'SwiftHLSL': 1, 'SwiftHack': 1, 'SwiftLLVM': 1, 'SwiftAssembly': 1, 'SwiftCMake': 1, 'SwiftCuda': 1, 'SwiftOCaml': 1, 'SwiftAwk': 1, 'SwiftM4': 1, 'SwiftTeX': 1, 'SwiftEmacs Lisp': 1, 'SwiftSmalltalk': 1, 'SwiftPawn': 1, 'SwiftCool': 1, 'SwiftVim script': 1, 'SwiftFortran': 1, 'SwiftMathematica': 1, 'SwiftM': 1, 'SwiftSuperCollider': 1, 'SwiftCommon Lisp': 1, 'SwiftAppleScript': 1, 'SwiftMercury': 1, 'SwiftPascal': 1, 'SwiftForth': 1, 'SwiftRenderScript': 1, 'SwiftDTrace': 1, 'SwiftLogos': 1, 'LuaHLSL': 1, 'LuaHack': 1, 'HLSLHack': 1, 'LLVMAssembly': 1, 'LLVMCMake': 1, 'LLVMCuda': 1, 'LLVMOCaml': 1, 'LLVMAwk': 1, 'LLVMM4': 1, 'LLVMTeX': 1, 'LLVMEmacs Lisp': 1, 'LLVMSmalltalk': 1, 'LLVMPawn': 1, 'LLVMCool': 1, 'LLVMVim script': 1, 'LLVMFortran': 1, 'LLVMMathematica': 1, 'LLVMM': 1, 'LLVMSuperCollider': 1, 'LLVMCommon Lisp': 1, 'LLVMAppleScript': 1, 'LLVMMercury': 1, 'LLVMPascal': 1, 'LLVMForth': 1, 'LLVMRenderScript': 1, 'LLVMDTrace': 1, 'LLVMLogos': 1, 'AssemblyCMake': 1, 'AssemblyCuda': 1, 'AssemblyOCaml': 1, 'AssemblyAwk': 1, 'AssemblyM4': 1, 'AssemblyTeX': 1, 'AssemblyEmacs Lisp': 1, 'AssemblySmalltalk': 1, 'AssemblyPawn': 1, 'AssemblyCool': 1, 'AssemblyVim script': 1, 'AssemblyFortran': 1, 'AssemblyMathematica': 1, 'AssemblyM': 1, 'AssemblySuperCollider': 1, 'AssemblyCommon Lisp': 1, 'AssemblyAppleScript': 1, 'AssemblyMercury': 1, 'AssemblyPascal': 1, 'AssemblyForth': 1, 'AssemblyRenderScript': 1, 'AssemblyDTrace': 1, 'AssemblyLogos': 1, 'AssemblyV': 1, 'CMakeCuda': 1, 'CMakeOCaml': 1, 'CMakeAwk': 1, 'CMakeM4': 1, 'CMakeTeX': 1, 'CMakeEmacs Lisp': 1, 'CMakeSmalltalk': 1, 'CMakePawn': 1, 'CMakeCool': 1, 'CMakeVim script': 1, 'CMakeFortran': 1, 'CMakeMathematica': 1, 'CMakeM': 1, 'CMakeSuperCollider': 1, 'CMakeCommon Lisp': 1, 'CMakeAppleScript': 1, 'CMakeMercury': 1, 'CMakePascal': 1, 'CMakeForth': 1, 'CMakeRenderScript': 1, 'CMakeDTrace': 1, 'CMakeLogos': 1, 'CudaOCaml': 1, 'CudaAwk': 1, 'CudaM4': 1, 'CudaTeX': 1, 'CudaEmacs Lisp': 1, 'CudaSmalltalk': 1, 'CudaPawn': 1, 'CudaCool': 1, 'CudaVim script': 1, 'CudaFortran': 1, 'CudaMathematica': 1, 'CudaM': 1, 'CudaSuperCollider': 1, 'CudaCommon Lisp': 1, 'CudaAppleScript': 1, 'CudaMercury': 1, 'CudaPascal': 1, 'CudaForth': 1, 'CudaRenderScript': 1, 'CudaDTrace': 1, 'CudaLogos': 1, 'OCamlAwk': 1, 'OCamlM4': 1, 'OCamlTeX': 1, 'OCamlEmacs Lisp': 1, 'OCamlSmalltalk': 1, 'OCamlPawn': 1, 'OCamlCool': 1, 'OCamlVim script': 1, 'OCamlFortran': 1, 'OCamlMathematica': 1, 'OCamlM': 1, 'OCamlSuperCollider': 1, 'OCamlCommon Lisp': 1, 'OCamlAppleScript': 1, 'OCamlMercury': 1, 'OCamlPascal': 1, 'OCamlForth': 1, 'OCamlRenderScript': 1, 'OCamlDTrace': 1, 'OCamlLogos': 1, 'AwkM4': 1, 'AwkTeX': 1, 'AwkEmacs Lisp': 1, 'AwkSmalltalk': 1, 'AwkPawn': 1, 'AwkCool': 1, 'AwkVim script': 1, 'AwkFortran': 1, 'AwkMathematica': 1, 'AwkM': 1, 'AwkSuperCollider': 1, 'AwkCommon Lisp': 1, 'AwkAppleScript': 1, 'AwkMercury': 1, 'AwkPascal': 1, 'AwkForth': 1, 'AwkRenderScript': 1, 'AwkDTrace': 1, 'AwkLogos': 1, 'M4TeX': 1, 'M4Emacs Lisp': 1, 'M4Smalltalk': 1, 'M4Pawn': 1, 'M4Cool': 1, 'M4Vim script': 1, 'M4Fortran': 1, 'M4Mathematica': 1, 'M4M': 1, 'M4SuperCollider': 1, 'M4Common Lisp': 1, 'M4AppleScript': 1, 'M4Mercury': 1, 'M4Pascal': 1, 'M4Forth': 1, 'M4RenderScript': 1, 'M4DTrace': 1, 'M4Logos': 1, 'TeXEmacs Lisp': 1, 'TeXSmalltalk': 1, 'TeXPawn': 1, 'TeXCool': 1, 'TeXVim script': 1, 'TeXFortran': 1, 'TeXMathematica': 1, 'TeXM': 1, 'TeXSuperCollider': 1, 'TeXCommon Lisp': 1, 'TeXAppleScript': 1, 'TeXMercury': 1, 'TeXPascal': 1, 'TeXForth': 1, 'TeXRenderScript': 1, 'TeXDTrace': 1, 'TeXLogos': 1, 'Emacs LispSmalltalk': 1, 'Emacs LispPawn': 1, 'Emacs LispCool': 1, 'Emacs LispVim script': 1, 'Emacs LispFortran': 1, 'Emacs LispMathematica': 1, 'Emacs LispM': 1, 'Emacs LispSuperCollider': 1, 'Emacs LispCommon Lisp': 1, 'Emacs LispAppleScript': 1, 'Emacs LispMercury': 1, 'Emacs LispPascal': 1, 'Emacs LispForth': 1, 'Emacs LispRenderScript': 1, 'Emacs LispDTrace': 1, 'Emacs LispLogos': 1, 'SmalltalkPawn': 1, 'SmalltalkCool': 1, 'SmalltalkVim script': 1, 'SmalltalkFortran': 1, 'SmalltalkMathematica': 1, 'SmalltalkM': 1, 'SmalltalkSuperCollider': 1, 'SmalltalkCommon Lisp': 1, 'SmalltalkAppleScript': 1, 'SmalltalkMercury': 1, 'SmalltalkPascal': 1, 'SmalltalkForth': 1, 'SmalltalkRenderScript': 1, 'SmalltalkDTrace': 1, 'SmalltalkLogos': 1, 'PawnCool': 1, 'PawnVim script': 1, 'PawnFortran': 1, 'PawnMathematica': 1, 'PawnM': 1, 'PawnSuperCollider': 1, 'PawnCommon Lisp': 1, 'PawnAppleScript': 1, 'PawnMercury': 1, 'PawnPascal': 1, 'PawnForth': 1, 'PawnRenderScript': 1, 'PawnDTrace': 1, 'PawnLogos': 1, 'CoolVim script': 1, 'CoolFortran': 1, 'CoolMathematica': 1, 'CoolM': 1, 'CoolSuperCollider': 1, 'CoolCommon Lisp': 1, 'CoolAppleScript': 1, 'CoolMercury': 1, 'CoolPascal': 1, 'CoolForth': 1, 'CoolRenderScript': 1, 'CoolDTrace': 1, 'CoolLogos': 1, 'Vim scriptFortran': 1, 'Vim scriptMathematica': 1, 'Vim scriptM': 1, 'Vim scriptSuperCollider': 1, 'Vim scriptCommon Lisp': 1, 'Vim scriptAppleScript': 1, 'Vim scriptMercury': 1, 'Vim scriptPascal': 1, 'Vim scriptForth': 1, 'Vim scriptRenderScript': 1, 'Vim scriptDTrace': 1, 'Vim scriptLogos': 1, 'FortranMathematica': 1, 'FortranM': 1, 'FortranSuperCollider': 1, 'FortranCommon Lisp': 1, 'FortranAppleScript': 1, 'FortranMercury': 1, 'FortranPascal': 1, 'FortranForth': 1, 'FortranRenderScript': 1, 'FortranDTrace': 1, 'FortranLogos': 1, 'MathematicaM': 1, 'MathematicaSuperCollider': 1, 'MathematicaCommon Lisp': 1, 'MathematicaAppleScript': 1, 'MathematicaMercury': 1, 'MathematicaPascal': 1, 'MathematicaForth': 1, 'MathematicaRenderScript': 1, 'MathematicaDTrace': 1, 'MathematicaLogos': 1, 'MSuperCollider': 1, 'MCommon Lisp': 1, 'MAppleScript': 1, 'MMercury': 1, 'MPascal': 1, 'MForth': 1, 'MRenderScript': 1, 'MDTrace': 1, 'MLogos': 1, 'SuperColliderCommon Lisp': 1, 'SuperColliderAppleScript': 1, 'SuperColliderMercury': 1, 'SuperColliderPascal': 1, 'SuperColliderForth': 1, 'SuperColliderRenderScript': 1, 'SuperColliderDTrace': 1, 'SuperColliderLogos': 1, 'Common LispAppleScript': 1, 'Common LispMercury': 1, 'Common LispPascal': 1, 'Common LispForth': 1, 'Common LispRenderScript': 1, 'Common LispDTrace': 1, 'Common LispLogos': 1, 'AppleScriptMercury': 1, 'AppleScriptPascal': 1, 'AppleScriptForth': 1, 'AppleScriptRenderScript': 1, 'AppleScriptDTrace': 1, 'AppleScriptLogos': 1, 'MercuryPascal': 1, 'MercuryForth': 1, 'MercuryRenderScript': 1, 'MercuryDTrace': 1, 'MercuryLogos': 1, 'PascalForth': 1, 'PascalRenderScript': 1, 'PascalDTrace': 1, 'PascalLogos': 1, 'ForthRenderScript': 1, 'ForthDTrace': 1, 'ForthLogos': 1, 'RenderScriptDTrace': 1, 'RenderScriptLogos': 1, 'DTraceLogos': 1, 'VuePLpgSQL': 1, 'VueTSQL': 1, 'PLpgSQLTSQL': 1, 'ASPXSLT': 1, 'KotlinProlog': 1}


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


    popdict = {2: 280, 1: 1067, 0: 3548, 20: 2, 10: 20, 21: 4, 4: 50, 11: 13, 9: 19, 12: 6, 8: 14, 5: 46, 13: 8, 3: 112, 6: 22, 24: 8, 23: 1, 15: 5, 17: 5, 7: 15, 25: 6, 14: 1, 16: 1}
    lang_dict = {'Jupyter NotebookPython': 2, 'Jupyter NotebookJavaScript': 1, 'Jupyter NotebookC++': 1, 'Jupyter NotebookShell': 2, 'Jupyter NotebookMATLAB': 2, 'Jupyter NotebookHTML': 2, 'Jupyter NotebookJava': 1, 'Jupyter NotebookCSS': 2, 'Jupyter NotebookDockerfile': 1, 'Jupyter NotebookMakefile': 2, 'Jupyter NotebookTypeScript': 1, 'Jupyter NotebookBatchfile': 1, 'Jupyter NotebookRuby': 1, 'Jupyter NotebookObjective-C': 1, 'Jupyter NotebookPerl 6': 1, 'Jupyter NotebookPerl': 1, 'Jupyter NotebookC': 1, 'Jupyter NotebookSwift': 1, 'Jupyter NotebookLua': 1, 'Jupyter NotebookCuda': 1, 'Jupyter NotebookAwk': 1, 'Jupyter NotebookTeX': 2, 'Jupyter NotebookVim script': 1, 'Jupyter NotebookM': 1, 'Jupyter NotebookProlog': 1, 'Jupyter NotebookB+NULL': 2, 'Jupyter NotebookOpenEdge ABL': 1, 'Jupyter NotebookMetal': 1, 'PythonJavaScript': 20, 'PythonC++': 10, 'PythonShell': 21, 'PythonMATLAB': 4, 'PythonHTML': 21, 'PythonJava': 11, 'PythonCSS': 21, 'PythonDockerfile': 9, 'PythonGo': 9, 'PythonMakefile': 20, 'PythonSmarty': 1, 'PythonTypeScript': 12, 'PythonBatchfile': 10, 'PythonPowerShell': 8, 'PythonGroovy': 5, 'PythonRuby': 13, 'PythonObjective-C': 10, 'PythonObjective-C++': 3, 'PythonClojure': 1, 'PythonPerl 6': 1, 'PythonPHP': 5, 'PythonVisual Basic': 1, 'PythonPerl': 9, 'PythonC': 13, 'PythonF#': 1, 'PythonCoffeeScript': 6, 'PythonRust': 1, 'PythonC#': 9, 'PythonR': 1, 'PythonRoff': 4, 'PythonSwift': 5, 'PythonLua': 1, 'PythonAssembly': 3, 'PythonCMake': 3, 'PythonCuda': 1, 'PythonOCaml': 1, 'PythonAwk': 3, 'PythonTeX': 3, 'PythonSmalltalk': 2, 'PythonVim script': 5, 'PythonFortran': 1, 'PythonM': 1, 'PythonAppleScript': 2, 'PythonPascal': 1, 'PythonVue': 1, 'PythonTSQL': 1, 'PythonASP': 3, 'PythonXSLT': 3, 'PythonKotlin': 2, 'PythonProlog': 2, 'PythonB+NULL': 21, 'PythonDart': 4, 'PythonProtocol Buffer': 3, 'PythonTcl': 2, 'PythonDIGITAL Command Language': 2, 'PythonSQLPL': 1, 'PythonGLSL': 2, 'PythonOpenEdge ABL': 2, 'PythonMetal': 1, 'PythonPostScript': 1, 'PythonHCL': 3, 'PythonXML': 1, 'PythonANTLR': 1, 'PythonThrift': 1, 'PythonLex': 1, 'PythonScala': 2, 'PythonD': 1, 'PythonHaskell': 1, 'PythonIDL': 1, 'PythonYacc': 1, 'PythonNginx': 2, 'PythonCOBOL': 1, 'PythonSaltStack': 1, 'PythonPLSQL': 1, 'PythonPuppet': 1, 'PythonGAP': 1, 'PythonGherkin': 1, 'PythonBoo': 1, 'PythonGnuplot': 1, 'PythonErlang': 1, 'Python1C Enterprise': 1, 'JavaScriptC++': 10, 'JavaScriptShell': 24, 'JavaScriptMATLAB': 3, 'JavaScriptHTML': 24, 'JavaScriptJava': 11, 'JavaScriptCSS': 24, 'JavaScriptDockerfile': 9, 'JavaScriptGo': 10, 'JavaScriptMakefile': 23, 'JavaScriptSmarty': 2, 'JavaScriptTypeScript': 15, 'JavaScriptBatchfile': 9, 'JavaScriptPowerShell': 8, 'JavaScriptGroovy': 5, 'JavaScriptRuby': 17, 'JavaScriptObjective-C': 11, 'JavaScriptObjective-C++': 3, 'JavaScriptClojure': 1, 'JavaScriptPHP': 5, 'JavaScriptVisual Basic': 1, 'JavaScriptPerl': 8, 'JavaScriptC': 12, 'JavaScriptF#': 1, 'JavaScriptCoffeeScript': 7, 'JavaScriptRust': 1, 'JavaScriptC#': 9, 'JavaScriptR': 1, 'JavaScriptRoff': 4, 'JavaScriptSwift': 5, 'JavaScriptLua': 2, 'JavaScriptAssembly': 3, 'JavaScriptCMake': 3, 'JavaScriptOCaml': 2, 'JavaScriptAwk': 2, 'JavaScriptTeX': 3, 'JavaScriptSmalltalk': 2, 'JavaScriptVim script': 4, 'JavaScriptFortran': 1, 'JavaScriptAppleScript': 3, 'JavaScriptPascal': 1, 'JavaScriptVue': 2, 'JavaScriptTSQL': 1, 'JavaScriptASP': 3, 'JavaScriptXSLT': 3, 'JavaScriptKotlin': 2, 'JavaScriptProlog': 1, 'JavaScriptB+NULL': 24, 'JavaScriptDart': 4, 'JavaScriptProtocol Buffer': 3, 'JavaScriptTcl': 2, 'JavaScriptDIGITAL Command Language': 2, 'JavaScriptSQLPL': 1, 'JavaScriptGLSL': 2, 'JavaScriptOpenEdge ABL': 2, 'JavaScriptMetal': 1, 'JavaScriptPostScript': 1, 'JavaScriptHCL': 3, 'JavaScriptXML': 1, 'JavaScriptANTLR': 1, 'JavaScriptThrift': 1, 'JavaScriptLex': 1, 'JavaScriptScala': 2, 'JavaScriptD': 1, 'JavaScriptHaskell': 1, 'JavaScriptIDL': 1, 'JavaScriptYacc': 1, 'JavaScriptNginx': 2, 'JavaScriptCOBOL': 1, 'JavaScriptSaltStack': 1, 'JavaScriptCrystal': 1, 'JavaScriptPLSQL': 1, 'JavaScriptPuppet': 1, 'JavaScriptGAP': 1, 'JavaScriptGherkin': 1, 'JavaScriptBoo': 1, 'JavaScriptGnuplot': 1, 'JavaScriptErlang': 1, 'JavaScript1C Enterprise': 1, 'C++Shell': 11, 'C++MATLAB': 2, 'C++HTML': 11, 'C++Java': 6, 'C++CSS': 11, 'C++Dockerfile': 6, 'C++Go': 4, 'C++Makefile': 11, 'C++TypeScript': 6, 'C++Batchfile': 6, 'C++PowerShell': 5, 'C++Groovy': 2, 'C++Ruby': 5, 'C++Objective-C': 7, 'C++Objective-C++': 3, 'C++Clojure': 1, 'C++Perl 6': 1, 'C++PHP': 2, 'C++Visual Basic': 1, 'C++Perl': 4, 'C++C': 9, 'C++CoffeeScript': 1, 'C++Rust': 1, 'C++C#': 5, 'C++Roff': 3, 'C++Swift': 2, 'C++Assembly': 3, 'C++CMake': 3, 'C++Cuda': 1, 'C++OCaml': 2, 'C++Awk': 2, 'C++TeX': 2, 'C++Smalltalk': 2, 'C++Vim script': 3, 'C++Fortran': 1, 'C++M': 1, 'C++AppleScript': 2, 'C++Vue': 1, 'C++TSQL': 1, 'C++ASP': 2, 'C++XSLT': 2, 'C++Kotlin': 2, 'C++Prolog': 2, 'C++B+NULL': 11, 'C++Dart': 3, 'C++Protocol Buffer': 1, 'C++Tcl': 2, 'C++DIGITAL Command Language': 2, 'C++SQLPL': 1, 'C++GLSL': 2, 'C++OpenEdge ABL': 1, 'C++XML': 1, 'C++ANTLR': 1, 'C++Thrift': 1, 'C++Lex': 1, 'C++Scala': 1, 'C++D': 1, 'C++Haskell': 1, 'C++IDL': 1, 'C++Yacc': 1, 'C++GAP': 1, 'C++Gherkin': 1, 'C++Boo': 1, 'C++1C Enterprise': 1, 'ShellMATLAB': 4, 'ShellHTML': 25, 'ShellJava': 12, 'ShellCSS': 25, 'ShellDockerfile': 10, 'ShellGo': 10, 'ShellMakefile': 24, 'ShellSmarty': 2, 'ShellTypeScript': 15, 'ShellBatchfile': 10, 'ShellPowerShell': 8, 'ShellGroovy': 5, 'ShellRuby': 17, 'ShellObjective-C': 11, 'ShellObjective-C++': 3, 'ShellClojure': 1, 'ShellPerl 6': 1, 'ShellPHP': 5, 'ShellVisual Basic': 1, 'ShellPerl': 9, 'ShellC': 13, 'ShellF#': 1, 'ShellCoffeeScript': 7, 'ShellRust': 1, 'ShellC#': 9, 'ShellR': 1, 'ShellRoff': 4, 'ShellSwift': 5, 'ShellLua': 2, 'ShellAssembly': 3, 'ShellCMake': 3, 'ShellCuda': 1, 'ShellOCaml': 2, 'ShellAwk': 3, 'ShellTeX': 4, 'ShellSmalltalk': 2, 'ShellVim script': 5, 'ShellFortran': 1, 'ShellM': 1, 'ShellAppleScript': 3, 'ShellPascal': 1, 'ShellVue': 2, 'ShellTSQL': 1, 'ShellASP': 3, 'ShellXSLT': 3, 'ShellKotlin': 2, 'ShellProlog': 2, 'ShellB+NULL': 25, 'ShellDart': 4, 'ShellProtocol Buffer': 3, 'ShellTcl': 2, 'ShellDIGITAL Command Language': 2, 'ShellSQLPL': 1, 'ShellGLSL': 2, 'ShellOpenEdge ABL': 2, 'ShellMetal': 1, 'ShellPostScript': 1, 'ShellHCL': 3, 'ShellXML': 1, 'ShellANTLR': 1, 'ShellThrift': 1, 'ShellLex': 1, 'ShellScala': 2, 'ShellD': 1, 'ShellHaskell': 1, 'ShellIDL': 1, 'ShellYacc': 1, 'ShellNginx': 2, 'ShellCOBOL': 1, 'ShellSaltStack': 1, 'ShellCrystal': 1, 'ShellPLSQL': 1, 'ShellPuppet': 1, 'ShellGAP': 1, 'ShellGherkin': 1, 'ShellBoo': 1, 'ShellGnuplot': 1, 'ShellErlang': 1, 'Shell1C Enterprise': 1, 'MATLABHTML': 4, 'MATLABJava': 3, 'MATLABCSS': 4, 'MATLABDockerfile': 2, 'MATLABGo': 2, 'MATLABMakefile': 4, 'MATLABTypeScript': 1, 'MATLABBatchfile': 2, 'MATLABPowerShell': 1, 'MATLABGroovy': 2, 'MATLABRuby': 2, 'MATLABObjective-C': 2, 'MATLABObjective-C++': 1, 'MATLABPerl 6': 1, 'MATLABPerl': 2, 'MATLABC': 2, 'MATLABCoffeeScript': 1, 'MATLABRust': 1, 'MATLABC#': 2, 'MATLABRoff': 1, 'MATLABSwift': 2, 'MATLABLua': 1, 'MATLABAssembly': 1, 'MATLABCuda': 1, 'MATLABOCaml': 1, 'MATLABAwk': 1, 'MATLABTeX': 2, 'MATLABSmalltalk': 1, 'MATLABVim script': 1, 'MATLABM': 1, 'MATLABKotlin': 1, 'MATLABProlog': 2, 'MATLABB+NULL': 4, 'MATLABOpenEdge ABL': 1, 'MATLABMetal': 1, 'MATLABXML': 1, 'MATLABANTLR': 1, 'MATLABThrift': 1, 'MATLABLex': 1, 'MATLABScala': 1, 'MATLABD': 1, 'MATLABHaskell': 1, 'MATLABIDL': 1, 'MATLABYacc': 1, 'HTMLJava': 12, 'HTMLCSS': 25, 'HTMLDockerfile': 10, 'HTMLGo': 10, 'HTMLMakefile': 24, 'HTMLSmarty': 2, 'HTMLTypeScript': 15, 'HTMLBatchfile': 10, 'HTMLPowerShell': 8, 'HTMLGroovy': 5, 'HTMLRuby': 17, 'HTMLObjective-C': 11, 'HTMLObjective-C++': 3, 'HTMLClojure': 1, 'HTMLPerl 6': 1, 'HTMLPHP': 5, 'HTMLVisual Basic': 1, 'HTMLPerl': 9, 'HTMLC': 13, 'HTMLF#': 1, 'HTMLCoffeeScript': 7, 'HTMLRust': 1, 'HTMLC#': 9, 'HTMLR': 1, 'HTMLRoff': 4, 'HTMLSwift': 5, 'HTMLLua': 2, 'HTMLAssembly': 3, 'HTMLCMake': 3, 'HTMLCuda': 1, 'HTMLOCaml': 2, 'HTMLAwk': 3, 'HTMLTeX': 4, 'HTMLSmalltalk': 2, 'HTMLVim script': 5, 'HTMLFortran': 1, 'HTMLM': 1, 'HTMLAppleScript': 3, 'HTMLPascal': 1, 'HTMLVue': 2, 'HTMLTSQL': 1, 'HTMLASP': 3, 'HTMLXSLT': 3, 'HTMLKotlin': 2, 'HTMLProlog': 2, 'HTMLB+NULL': 25, 'HTMLDart': 4, 'HTMLProtocol Buffer': 3, 'HTMLTcl': 2, 'HTMLDIGITAL Command Language': 2, 'HTMLSQLPL': 1, 'HTMLGLSL': 2, 'HTMLOpenEdge ABL': 2, 'HTMLMetal': 1, 'HTMLPostScript': 1, 'HTMLHCL': 3, 'HTMLXML': 1, 'HTMLANTLR': 1, 'HTMLThrift': 1, 'HTMLLex': 1, 'HTMLScala': 2, 'HTMLD': 1, 'HTMLHaskell': 1, 'HTMLIDL': 1, 'HTMLYacc': 1, 'HTMLNginx': 2, 'HTMLCOBOL': 1, 'HTMLSaltStack': 1, 'HTMLCrystal': 1, 'HTMLPLSQL': 1, 'HTMLPuppet': 1, 'HTMLGAP': 1, 'HTMLGherkin': 1, 'HTMLBoo': 1, 'HTMLGnuplot': 1, 'HTMLErlang': 1, 'HTML1C Enterprise': 1, 'JavaCSS': 12, 'JavaDockerfile': 8, 'JavaGo': 5, 'JavaMakefile': 11, 'JavaSmarty': 2, 'JavaTypeScript': 7, 'JavaBatchfile': 7, 'JavaPowerShell': 4, 'JavaGroovy': 3, 'JavaRuby': 9, 'JavaObjective-C': 8, 'JavaObjective-C++': 1, 'JavaPerl 6': 1, 'JavaPHP': 3, 'JavaPerl': 4, 'JavaC': 8, 'JavaF#': 1, 'JavaCoffeeScript': 4, 'JavaRust': 1, 'JavaC#': 8, 'JavaR': 1, 'JavaRoff': 2, 'JavaSwift': 3, 'JavaAssembly': 2, 'JavaCMake': 2, 'JavaCuda': 1, 'JavaOCaml': 1, 'JavaAwk': 1, 'JavaTeX': 2, 'JavaSmalltalk': 2, 'JavaVim script': 2, 'JavaM': 1, 'JavaAppleScript': 1, 'JavaVue': 1, 'JavaTSQL': 1, 'JavaASP': 2, 'JavaXSLT': 2, 'JavaKotlin': 2, 'JavaProlog': 2, 'JavaB+NULL': 12, 'JavaDart': 2, 'JavaProtocol Buffer': 2, 'JavaTcl': 2, 'JavaDIGITAL Command Language': 1, 'JavaSQLPL': 1, 'JavaGLSL': 2, 'JavaHCL': 1, 'JavaXML': 1, 'JavaANTLR': 1, 'JavaThrift': 1, 'JavaLex': 1, 'JavaScala': 2, 'JavaD': 1, 'JavaHaskell': 1, 'JavaIDL': 1, 'JavaYacc': 1, 'JavaNginx': 2, 'JavaCOBOL': 1, 'JavaSaltStack': 1, 'JavaGAP': 1, 'JavaGherkin': 1, 'JavaBoo': 1, 'CSSDockerfile': 10, 'CSSGo': 10, 'CSSMakefile': 24, 'CSSSmarty': 2, 'CSSTypeScript': 15, 'CSSBatchfile': 10, 'CSSPowerShell': 8, 'CSSGroovy': 5, 'CSSRuby': 17, 'CSSObjective-C': 11, 'CSSObjective-C++': 3, 'CSSClojure': 1, 'CSSPerl 6': 1, 'CSSPHP': 5, 'CSSVisual Basic': 1, 'CSSPerl': 9, 'CSSC': 13, 'CSSF#': 1, 'CSSCoffeeScript': 7, 'CSSRust': 1, 'CSSC#': 9, 'CSSR': 1, 'CSSRoff': 4, 'CSSSwift': 5, 'CSSLua': 2, 'CSSAssembly': 3, 'CSSCMake': 3, 'CSSCuda': 1, 'CSSOCaml': 2, 'CSSAwk': 3, 'CSSTeX': 4, 'CSSSmalltalk': 2, 'CSSVim script': 5, 'CSSFortran': 1, 'CSSM': 1, 'CSSAppleScript': 3, 'CSSPascal': 1, 'CSSVue': 2, 'CSSTSQL': 1, 'CSSASP': 3, 'CSSXSLT': 3, 'CSSKotlin': 2, 'CSSProlog': 2, 'CSSB+NULL': 25, 'CSSDart': 4, 'CSSProtocol Buffer': 3, 'CSSTcl': 2, 'CSSDIGITAL Command Language': 2, 'CSSSQLPL': 1, 'CSSGLSL': 2, 'CSSOpenEdge ABL': 2, 'CSSMetal': 1, 'CSSPostScript': 1, 'CSSHCL': 3, 'CSSXML': 1, 'CSSANTLR': 1, 'CSSThrift': 1, 'CSSLex': 1, 'CSSScala': 2, 'CSSD': 1, 'CSSHaskell': 1, 'CSSIDL': 1, 'CSSYacc': 1, 'CSSNginx': 2, 'CSSCOBOL': 1, 'CSSSaltStack': 1, 'CSSCrystal': 1, 'CSSPLSQL': 1, 'CSSPuppet': 1, 'CSSGAP': 1, 'CSSGherkin': 1, 'CSSBoo': 1, 'CSSGnuplot': 1, 'CSSErlang': 1, 'CSS1C Enterprise': 1, 'DockerfileGo': 6, 'DockerfileMakefile': 10, 'DockerfileSmarty': 1, 'DockerfileTypeScript': 6, 'DockerfileBatchfile': 6, 'DockerfilePowerShell': 4, 'DockerfileGroovy': 2, 'DockerfileRuby': 7, 'DockerfileObjective-C': 5, 'DockerfileObjective-C++': 1, 'DockerfilePerl 6': 1, 'DockerfilePHP': 2, 'DockerfilePerl': 4, 'DockerfileC': 7, 'DockerfileF#': 1, 'DockerfileCoffeeScript': 2, 'DockerfileRust': 1, 'DockerfileC#': 5, 'DockerfileR': 1, 'DockerfileRoff': 2, 'DockerfileSwift': 3, 'DockerfileAssembly': 2, 'DockerfileCMake': 1, 'DockerfileCuda': 1, 'DockerfileOCaml': 2, 'DockerfileAwk': 1, 'DockerfileTeX': 2, 'DockerfileSmalltalk': 1, 'DockerfileVim script': 2, 'DockerfileM': 1, 'DockerfileAppleScript': 2, 'DockerfilePascal': 1, 'DockerfileTSQL': 1, 'DockerfileASP': 1, 'DockerfileXSLT': 1, 'DockerfileKotlin': 2, 'DockerfileProlog': 2, 'DockerfileB+NULL': 10, 'DockerfileDart': 2, 'DockerfileProtocol Buffer': 1, 'DockerfileTcl': 1, 'DockerfileDIGITAL Command Language': 1, 'DockerfileSQLPL': 1, 'DockerfileGLSL': 1, 'DockerfileHCL': 2, 'DockerfileXML': 1, 'DockerfileANTLR': 1, 'DockerfileThrift': 1, 'DockerfileLex': 1, 'DockerfileScala': 2, 'DockerfileD': 1, 'DockerfileHaskell': 1, 'DockerfileIDL': 1, 'DockerfileYacc': 1, 'DockerfileNginx': 2, 'DockerfileCOBOL': 1, 'DockerfileSaltStack': 1, 'DockerfilePLSQL': 1, 'DockerfilePuppet': 1, 'GoMakefile': 10, 'GoSmarty': 1, 'GoTypeScript': 4, 'GoBatchfile': 5, 'GoPowerShell': 4, 'GoGroovy': 3, 'GoRuby': 7, 'GoObjective-C': 2, 'GoObjective-C++': 1, 'GoPHP': 3, 'GoPerl': 6, 'GoC': 5, 'GoF#': 1, 'GoCoffeeScript': 4, 'GoRust': 1, 'GoC#': 5, 'GoR': 1, 'GoRoff': 3, 'GoSwift': 2, 'GoAssembly': 3, 'GoCMake': 1, 'GoOCaml': 2, 'GoAwk': 1, 'GoTeX': 1, 'GoSmalltalk': 1, 'GoVim script': 1, 'GoFortran': 1, 'GoAppleScript': 1, 'GoPascal': 1, 'GoTSQL': 1, 'GoASP': 1, 'GoXSLT': 1, 'GoKotlin': 1, 'GoProlog': 1, 'GoB+NULL': 10, 'GoDart': 1, 'GoProtocol Buffer': 1, 'GoTcl': 1, 'GoDIGITAL Command Language': 1, 'GoSQLPL': 1, 'GoGLSL': 1, 'GoPostScript': 1, 'GoHCL': 2, 'GoXML': 1, 'GoANTLR': 1, 'GoThrift': 1, 'GoLex': 1, 'GoScala': 2, 'GoD': 1, 'GoHaskell': 1, 'GoIDL': 1, 'GoYacc': 1, 'GoNginx': 2, 'GoCOBOL': 1, 'GoSaltStack': 1, 'GoPLSQL': 1, 'GoPuppet': 1, 'MakefileSmarty': 2, 'MakefileTypeScript': 14, 'MakefileBatchfile': 9, 'MakefilePowerShell': 8, 'MakefileGroovy': 5, 'MakefileRuby': 16, 'MakefileObjective-C': 10, 'MakefileObjective-C++': 3, 'MakefileClojure': 1, 'MakefilePerl 6': 1, 'MakefilePHP': 5, 'MakefileVisual Basic': 1, 'MakefilePerl': 9, 'MakefileC': 13, 'MakefileF#': 1, 'MakefileCoffeeScript': 6, 'MakefileRust': 1, 'MakefileC#': 8, 'MakefileR': 1, 'MakefileRoff': 4, 'MakefileSwift': 5, 'MakefileLua': 2, 'MakefileAssembly': 3, 'MakefileCMake': 3, 'MakefileCuda': 1, 'MakefileOCaml': 2, 'MakefileAwk': 3, 'MakefileTeX': 4, 'MakefileSmalltalk': 2, 'MakefileVim script': 5, 'MakefileFortran': 1, 'MakefileM': 1, 'MakefileAppleScript': 3, 'MakefilePascal': 1, 'MakefileVue': 2, 'MakefileTSQL': 1, 'MakefileASP': 3, 'MakefileXSLT': 3, 'MakefileKotlin': 2, 'MakefileProlog': 2, 'MakefileB+NULL': 24, 'MakefileDart': 4, 'MakefileProtocol Buffer': 2, 'MakefileTcl': 2, 'MakefileDIGITAL Command Language': 2, 'MakefileSQLPL': 1, 'MakefileGLSL': 2, 'MakefileOpenEdge ABL': 2, 'MakefileMetal': 1, 'MakefilePostScript': 1, 'MakefileHCL': 3, 'MakefileXML': 1, 'MakefileANTLR': 1, 'MakefileThrift': 1, 'MakefileLex': 1, 'MakefileScala': 2, 'MakefileD': 1, 'MakefileHaskell': 1, 'MakefileIDL': 1, 'MakefileYacc': 1, 'MakefileNginx': 2, 'MakefileCOBOL': 1, 'MakefileSaltStack': 1, 'MakefileCrystal': 1, 'MakefilePLSQL': 1, 'MakefilePuppet': 1, 'MakefileGAP': 1, 'MakefileGherkin': 1, 'MakefileBoo': 1, 'MakefileGnuplot': 1, 'MakefileErlang': 1, 'Makefile1C Enterprise': 1, 'SmartyTypeScript': 1, 'SmartyBatchfile': 1, 'SmartyPowerShell': 1, 'SmartyGroovy': 1, 'SmartyRuby': 2, 'SmartyObjective-C': 1, 'SmartyPHP': 1, 'SmartyPerl': 1, 'SmartyC': 1, 'SmartyF#': 1, 'SmartyCoffeeScript': 1, 'SmartyC#': 1, 'SmartyR': 1, 'SmartyVue': 1, 'SmartyXSLT': 1, 'SmartyB+NULL': 2, 'SmartyProtocol Buffer': 1, 'SmartyNginx': 1, 'SmartyCOBOL': 1, 'SmartySaltStack': 1, 'TypeScriptBatchfile': 6, 'TypeScriptPowerShell': 4, 'TypeScriptGroovy': 3, 'TypeScriptRuby': 13, 'TypeScriptObjective-C': 7, 'TypeScriptObjective-C++': 1, 'TypeScriptClojure': 1, 'TypeScriptPHP': 5, 'TypeScriptVisual Basic': 1, 'TypeScriptPerl': 5, 'TypeScriptC': 6, 'TypeScriptF#': 1, 'TypeScriptCoffeeScript': 6, 'TypeScriptC#': 6, 'TypeScriptR': 1, 'TypeScriptRoff': 2, 'TypeScriptSwift': 4, 'TypeScriptLua': 2, 'TypeScriptCMake': 2, 'TypeScriptOCaml': 1, 'TypeScriptAwk': 1, 'TypeScriptTeX': 2, 'TypeScriptSmalltalk': 1, 'TypeScriptVim script': 2, 'TypeScriptAppleScript': 3, 'TypeScriptASP': 3, 'TypeScriptXSLT': 3, 'TypeScriptKotlin': 1, 'TypeScriptB+NULL': 15, 'TypeScriptDart': 4, 'TypeScriptProtocol Buffer': 3, 'TypeScriptTcl': 1, 'TypeScriptDIGITAL Command Language': 1, 'TypeScriptGLSL': 1, 'TypeScriptOpenEdge ABL': 2, 'TypeScriptMetal': 1, 'TypeScriptPostScript': 1, 'TypeScriptHCL': 1, 'TypeScriptScala': 1, 'TypeScriptNginx': 2, 'TypeScriptCOBOL': 1, 'TypeScriptSaltStack': 1, 'TypeScriptCrystal': 1, 'TypeScriptGAP': 1, 'TypeScriptGherkin': 1, 'TypeScriptBoo': 1, 'TypeScriptGnuplot': 1, 'TypeScriptErlang': 1, 'TypeScript1C Enterprise': 1, 'BatchfilePowerShell': 6, 'BatchfileGroovy': 4, 'BatchfileRuby': 6, 'BatchfileObjective-C': 5, 'BatchfileObjective-C++': 2, 'BatchfileClojure': 1, 'BatchfilePerl 6': 1, 'BatchfilePHP': 2, 'BatchfileVisual Basic': 1, 'BatchfilePerl': 5, 'BatchfileC': 7, 'BatchfileF#': 1, 'BatchfileCoffeeScript': 4, 'BatchfileRust': 1, 'BatchfileC#': 6, 'BatchfileR': 1, 'BatchfileRoff': 3, 'BatchfileSwift': 2, 'BatchfileAssembly': 3, 'BatchfileCMake': 2, 'BatchfileCuda': 1, 'BatchfileOCaml': 1, 'BatchfileAwk': 3, 'BatchfileTeX': 2, 'BatchfileSmalltalk': 1, 'BatchfileVim script': 2, 'BatchfileFortran': 1, 'BatchfileM': 1, 'BatchfileAppleScript': 1, 'BatchfileTSQL': 1, 'BatchfileASP': 2, 'BatchfileXSLT': 2, 'BatchfileKotlin': 2, 'BatchfileProlog': 2, 'BatchfileB+NULL': 10, 'BatchfileDart': 3, 'BatchfileProtocol Buffer': 2, 'BatchfileTcl': 1, 'BatchfileDIGITAL Command Language': 2, 'BatchfileSQLPL': 1, 'BatchfileGLSL': 1, 'BatchfileOpenEdge ABL': 1, 'BatchfileXML': 1, 'BatchfileANTLR': 1, 'BatchfileThrift': 1, 'BatchfileLex': 1, 'BatchfileScala': 2, 'BatchfileD': 1, 'BatchfileHaskell': 1, 'BatchfileIDL': 1, 'BatchfileYacc': 1, 'BatchfileNginx': 2, 'BatchfileCOBOL': 1, 'BatchfileSaltStack': 1, 'BatchfileGnuplot': 1, 'BatchfileErlang': 1, 'Batchfile1C Enterprise': 1, 'PowerShellGroovy': 4, 'PowerShellRuby': 4, 'PowerShellObjective-C': 5, 'PowerShellObjective-C++': 3, 'PowerShellClojure': 1, 'PowerShellPHP': 1, 'PowerShellVisual Basic': 1, 'PowerShellPerl': 2, 'PowerShellC': 7, 'PowerShellF#': 1, 'PowerShellCoffeeScript': 2, 'PowerShellRust': 1, 'PowerShellC#': 4, 'PowerShellR': 1, 'PowerShellRoff': 3, 'PowerShellSwift': 2, 'PowerShellAssembly': 2, 'PowerShellCMake': 2, 'PowerShellOCaml': 1, 'PowerShellAwk': 1, 'PowerShellTeX': 1, 'PowerShellSmalltalk': 1, 'PowerShellVim script': 2, 'PowerShellAppleScript': 1, 'PowerShellVue': 1, 'PowerShellTSQL': 1, 'PowerShellASP': 1, 'PowerShellXSLT': 2, 'PowerShellKotlin': 2, 'PowerShellProlog': 1, 'PowerShellB+NULL': 8, 'PowerShellDart': 2, 'PowerShellProtocol Buffer': 1, 'PowerShellTcl': 1, 'PowerShellDIGITAL Command Language': 2, 'PowerShellSQLPL': 1, 'PowerShellGLSL': 1, 'PowerShellOpenEdge ABL': 1, 'PowerShellHCL': 1, 'PowerShellXML': 1, 'PowerShellANTLR': 1, 'PowerShellThrift': 1, 'PowerShellLex': 1, 'PowerShellScala': 1, 'PowerShellD': 1, 'PowerShellHaskell': 1, 'PowerShellIDL': 1, 'PowerShellYacc': 1, 'PowerShellNginx': 1, 'PowerShellCOBOL': 1, 'PowerShellSaltStack': 1, 'PowerShellGnuplot': 1, 'PowerShellErlang': 1, 'PowerShell1C Enterprise': 1, 'GroovyRuby': 3, 'GroovyObjective-C': 2, 'GroovyObjective-C++': 2, 'GroovyClojure': 1, 'GroovyPHP': 1, 'GroovyVisual Basic': 1, 'GroovyPerl': 3, 'GroovyC': 3, 'GroovyF#': 1, 'GroovyCoffeeScript': 3, 'GroovyRust': 1, 'GroovyC#': 4, 'GroovyR': 1, 'GroovyRoff': 2, 'GroovySwift': 1, 'GroovyAssembly': 1, 'GroovyCMake': 1, 'GroovyOCaml': 1, 'GroovyAwk': 1, 'GroovySmalltalk': 1, 'GroovyVim script': 1, 'GroovyAppleScript': 1, 'GroovyASP': 1, 'GroovyXSLT': 2, 'GroovyKotlin': 1, 'GroovyProlog': 1, 'GroovyB+NULL': 5, 'GroovyDart': 1, 'GroovyProtocol Buffer': 1, 'GroovyDIGITAL Command Language': 1, 'GroovyOpenEdge ABL': 1, 'GroovyXML': 1, 'GroovyANTLR': 1, 'GroovyThrift': 1, 'GroovyLex': 1, 'GroovyScala': 1, 'GroovyD': 1, 'GroovyHaskell': 1, 'GroovyIDL': 1, 'GroovyYacc': 1, 'GroovyNginx': 1, 'GroovyCOBOL': 1, 'GroovySaltStack': 1, 'GroovyGnuplot': 1, 'GroovyErlang': 1, 'Groovy1C Enterprise': 1, 'RubyObjective-C': 7, 'RubyPHP': 5, 'RubyPerl': 6, 'RubyC': 5, 'RubyF#': 1, 'RubyCoffeeScript': 6, 'RubyC#': 6, 'RubyR': 1, 'RubyRoff': 2, 'RubySwift': 4, 'RubyLua': 2, 'RubyAssembly': 1, 'RubyCMake': 2, 'RubyOCaml': 1, 'RubyAwk': 1, 'RubyTeX': 3, 'RubySmalltalk': 1, 'RubyAppleScript': 2, 'RubyPascal': 1, 'RubyVue': 1, 'RubyTSQL': 1, 'RubyASP': 2, 'RubyXSLT': 2, 'RubyKotlin': 1, 'RubyB+NULL': 17, 'RubyDart': 3, 'RubyProtocol Buffer': 3, 'RubyTcl': 2, 'RubyDIGITAL Command Language': 1, 'RubySQLPL': 1, 'RubyGLSL': 2, 'RubyOpenEdge ABL': 1, 'RubyMetal': 1, 'RubyPostScript': 1, 'RubyHCL': 2, 'RubyScala': 1, 'RubyNginx': 2, 'RubyCOBOL': 1, 'RubySaltStack': 1, 'RubyCrystal': 1, 'RubyPLSQL': 1, 'RubyPuppet': 1, 'RubyGAP': 1, 'RubyGherkin': 1, 'RubyBoo': 1, 'RubyGnuplot': 1, 'RubyErlang': 1, 'Objective-CObjective-C++': 3, 'Objective-CClojure': 1, 'Objective-CPHP': 1, 'Objective-CVisual Basic': 1, 'Objective-CPerl': 1, 'Objective-CC': 8, 'Objective-CCoffeeScript': 2, 'Objective-CRust': 1, 'Objective-CC#': 6, 'Objective-CRoff': 3, 'Objective-CSwift': 4, 'Objective-CLua': 1, 'Objective-CAssembly': 2, 'Objective-CCMake': 3, 'Objective-COCaml': 1, 'Objective-CTeX': 2, 'Objective-CSmalltalk': 2, 'Objective-CVim script': 2, 'Objective-CAppleScript': 1, 'Objective-CVue': 2, 'Objective-CTSQL': 1, 'Objective-CASP': 2, 'Objective-CXSLT': 2, 'Objective-CKotlin': 2, 'Objective-CProlog': 1, 'Objective-CB+NULL': 11, 'Objective-CDart': 2, 'Objective-CProtocol Buffer': 1, 'Objective-CTcl': 2, 'Objective-CDIGITAL Command Language': 2, 'Objective-CSQLPL': 1, 'Objective-CGLSL': 2, 'Objective-COpenEdge ABL': 2, 'Objective-CMetal': 1, 'Objective-CHCL': 1, 'Objective-CXML': 1, 'Objective-CANTLR': 1, 'Objective-CThrift': 1, 'Objective-CLex': 1, 'Objective-CScala': 1, 'Objective-CD': 1, 'Objective-CHaskell': 1, 'Objective-CIDL': 1, 'Objective-CYacc': 1, 'Objective-CGAP': 1, 'Objective-CGherkin': 1, 'Objective-CBoo': 1, 'Objective-C1C Enterprise': 1, 'Objective-C++Clojure': 1, 'Objective-C++Visual Basic': 1, 'Objective-C++Perl': 1, 'Objective-C++C': 3, 'Objective-C++CoffeeScript': 1, 'Objective-C++Rust': 1, 'Objective-C++C#': 2, 'Objective-C++Roff': 2, 'Objective-C++Swift': 1, 'Objective-C++Assembly': 1, 'Objective-C++CMake': 1, 'Objective-C++OCaml': 1, 'Objective-C++Smalltalk': 1, 'Objective-C++Vim script': 1, 'Objective-C++Vue': 1, 'Objective-C++ASP': 1, 'Objective-C++XSLT': 1, 'Objective-C++Kotlin': 1, 'Objective-C++Prolog': 1, 'Objective-C++B+NULL': 3, 'Objective-C++Dart': 1, 'Objective-C++DIGITAL Command Language': 1, 'Objective-C++OpenEdge ABL': 1, 'Objective-C++XML': 1, 'Objective-C++ANTLR': 1, 'Objective-C++Thrift': 1, 'Objective-C++Lex': 1, 'Objective-C++Scala': 1, 'Objective-C++D': 1, 'Objective-C++Haskell': 1, 'Objective-C++IDL': 1, 'Objective-C++Yacc': 1, 'Objective-C++1C Enterprise': 1, 'ClojureVisual Basic': 1, 'ClojurePerl': 1, 'ClojureC': 1, 'ClojureCoffeeScript': 1, 'ClojureC#': 1, 'ClojureRoff': 1, 'ClojureCMake': 1, 'ClojureVim script': 1, 'ClojureASP': 1, 'ClojureXSLT': 1, 'ClojureB+NULL': 1, 'ClojureDart': 1, 'ClojureDIGITAL Command Language': 1, 'ClojureOpenEdge ABL': 1, 'Clojure1C Enterprise': 1, 'Perl 6Perl': 1, 'Perl 6C': 1, 'Perl 6Cuda': 1, 'Perl 6Awk': 1, 'Perl 6TeX': 1, 'Perl 6Vim script': 1, 'Perl 6M': 1, 'Perl 6Prolog': 1, 'Perl 6B+NULL': 1, 'PHPPerl': 4, 'PHPC': 2, 'PHPF#': 1, 'PHPCoffeeScript': 3, 'PHPC#': 3, 'PHPR': 1, 'PHPRoff': 1, 'PHPSwift': 1, 'PHPCMake': 1, 'PHPSmalltalk': 1, 'PHPASP': 2, 'PHPXSLT': 2, 'PHPB+NULL': 5, 'PHPDart': 2, 'PHPProtocol Buffer': 2, 'PHPTcl': 1, 'PHPGLSL': 1, 'PHPPostScript': 1, 'PHPScala': 1, 'PHPNginx': 2, 'PHPCOBOL': 1, 'PHPSaltStack': 1, 'PHPGAP': 1, 'PHPGherkin': 1, 'PHPBoo': 1, 'Visual BasicPerl': 1, 'Visual BasicC': 1, 'Visual BasicCoffeeScript': 1, 'Visual BasicC#': 1, 'Visual BasicRoff': 1, 'Visual BasicCMake': 1, 'Visual BasicVim script': 1, 'Visual BasicASP': 1, 'Visual BasicXSLT': 1, 'Visual BasicB+NULL': 1, 'Visual BasicDart': 1, 'Visual BasicDIGITAL Command Language': 1, 'Visual BasicOpenEdge ABL': 1, 'Visual Basic1C Enterprise': 1, 'PerlC': 4, 'PerlF#': 1, 'PerlCoffeeScript': 5, 'PerlC#': 4, 'PerlR': 1, 'PerlRoff': 2, 'PerlSwift': 1, 'PerlAssembly': 1, 'PerlCMake': 1, 'PerlCuda': 1, 'PerlAwk': 2, 'PerlTeX': 1, 'PerlVim script': 2, 'PerlFortran': 1, 'PerlM': 1, 'PerlPascal': 1, 'PerlASP': 2, 'PerlXSLT': 2, 'PerlProlog': 1, 'PerlB+NULL': 9, 'PerlDart': 3, 'PerlProtocol Buffer': 2, 'PerlDIGITAL Command Language': 1, 'PerlOpenEdge ABL': 1, 'PerlPostScript': 1, 'PerlHCL': 1, 'PerlScala': 1, 'PerlNginx': 2, 'PerlCOBOL': 1, 'PerlSaltStack': 1, 'PerlPLSQL': 1, 'PerlPuppet': 1, 'Perl1C Enterprise': 1, 'CF#': 1, 'CCoffeeScript': 2, 'CRust': 1, 'CC#': 6, 'CR': 1, 'CRoff': 3, 'CSwift': 3, 'CAssembly': 3, 'CCMake': 3, 'CCuda': 1, 'COCaml': 1, 'CAwk': 2, 'CTeX': 2, 'CSmalltalk': 2, 'CVim script': 5, 'CFortran': 1, 'CM': 1, 'CAppleScript': 1, 'CVue': 1, 'CTSQL': 1, 'CASP': 2, 'CXSLT': 3, 'CKotlin': 2, 'CProlog': 2, 'CB+NULL': 13, 'CDart': 2, 'CProtocol Buffer': 1, 'CTcl': 2, 'CDIGITAL Command Language': 2, 'CSQLPL': 1, 'CGLSL': 2, 'COpenEdge ABL': 1, 'CHCL': 2, 'CXML': 1, 'CANTLR': 1, 'CThrift': 1, 'CLex': 1, 'CScala': 1, 'CD': 1, 'CHaskell': 1, 'CIDL': 1, 'CYacc': 1, 'CNginx': 1, 'CCOBOL': 1, 'CSaltStack': 1, 'CGAP': 1, 'CGherkin': 1, 'CBoo': 1, 'C1C Enterprise': 1, 'F#CoffeeScript': 1, 'F#C#': 1, 'F#R': 1, 'F#XSLT': 1, 'F#B+NULL': 1, 'F#Protocol Buffer': 1, 'F#Nginx': 1, 'F#COBOL': 1, 'F#SaltStack': 1, 'CoffeeScriptC#': 5, 'CoffeeScriptR': 1, 'CoffeeScriptRoff': 2, 'CoffeeScriptSwift': 1, 'CoffeeScriptLua': 1, 'CoffeeScriptCMake': 1, 'CoffeeScriptTeX': 1, 'CoffeeScriptVim script': 1, 'CoffeeScriptASP': 2, 'CoffeeScriptXSLT': 2, 'CoffeeScriptB+NULL': 7, 'CoffeeScriptDart': 2, 'CoffeeScriptProtocol Buffer': 2, 'CoffeeScriptDIGITAL Command Language': 1, 'CoffeeScriptOpenEdge ABL': 1, 'CoffeeScriptPostScript': 1, 'CoffeeScriptScala': 1, 'CoffeeScriptNginx': 2, 'CoffeeScriptCOBOL': 1, 'CoffeeScriptSaltStack': 1, 'CoffeeScriptCrystal': 1, 'CoffeeScript1C Enterprise': 1, 'RustC#': 1, 'RustRoff': 1, 'RustSwift': 1, 'RustAssembly': 1, 'RustOCaml': 1, 'RustSmalltalk': 1, 'RustKotlin': 1, 'RustProlog': 1, 'RustB+NULL': 1, 'RustXML': 1, 'RustANTLR': 1, 'RustThrift': 1, 'RustLex': 1, 'RustScala': 1, 'RustD': 1, 'RustHaskell': 1, 'RustIDL': 1, 'RustYacc': 1, 'C#R': 1, 'C#Roff': 3, 'C#Swift': 1, 'C#Assembly': 2, 'C#CMake': 3, 'C#OCaml': 1, 'C#TeX': 1, 'C#Smalltalk': 2, 'C#Vim script': 2, 'C#AppleScript': 1, 'C#TSQL': 1, 'C#ASP': 3, 'C#XSLT': 3, 'C#Kotlin': 1, 'C#Prolog': 1, 'C#B+NULL': 9, 'C#Dart': 2, 'C#Protocol Buffer': 2, 'C#Tcl': 2, 'C#DIGITAL Command Language': 2, 'C#SQLPL': 1, 'C#GLSL': 2, 'C#OpenEdge ABL': 1, 'C#XML': 1, 'C#ANTLR': 1, 'C#Thrift': 1, 'C#Lex': 1, 'C#Scala': 2, 'C#D': 1, 'C#Haskell': 1, 'C#IDL': 1, 'C#Yacc': 1, 'C#Nginx': 2, 'C#COBOL': 1, 'C#SaltStack': 1, 'C#GAP': 1, 'C#Gherkin': 1, 'C#Boo': 1, 'C#1C Enterprise': 1, 'RXSLT': 1, 'RB+NULL': 1, 'RProtocol Buffer': 1, 'RNginx': 1, 'RCOBOL': 1, 'RSaltStack': 1, 'RoffSwift': 2, 'RoffAssembly': 2, 'RoffCMake': 2, 'RoffOCaml': 1, 'RoffTeX': 1, 'RoffSmalltalk': 1, 'RoffVim script': 1, 'RoffTSQL': 1, 'RoffASP': 1, 'RoffXSLT': 1, 'RoffKotlin': 1, 'RoffProlog': 1, 'RoffB+NULL': 4, 'RoffDart': 1, 'RoffTcl': 1, 'RoffDIGITAL Command Language': 2, 'RoffSQLPL': 1, 'RoffGLSL': 1, 'RoffOpenEdge ABL': 1, 'RoffPostScript': 1, 'RoffXML': 1, 'RoffANTLR': 1, 'RoffThrift': 1, 'RoffLex': 1, 'RoffScala': 1, 'RoffD': 1, 'RoffHaskell': 1, 'RoffIDL': 1, 'RoffYacc': 1, 'Roff1C Enterprise': 1, 'SwiftLua': 1, 'SwiftAssembly': 1, 'SwiftOCaml': 1, 'SwiftTeX': 1, 'SwiftSmalltalk': 1, 'SwiftKotlin': 2, 'SwiftProlog': 1, 'SwiftB+NULL': 5, 'SwiftDart': 1, 'SwiftOpenEdge ABL': 1, 'SwiftMetal': 1, 'SwiftPostScript': 1, 'SwiftHCL': 1, 'SwiftXML': 1, 'SwiftANTLR': 1, 'SwiftThrift': 1, 'SwiftLex': 1, 'SwiftScala': 1, 'SwiftD': 1, 'SwiftHaskell': 1, 'SwiftIDL': 1, 'SwiftYacc': 1, 'LuaTeX': 2, 'LuaB+NULL': 2, 'LuaOpenEdge ABL': 1, 'LuaMetal': 1, 'LuaCrystal': 1, 'AssemblyCMake': 1, 'AssemblyOCaml': 1, 'AssemblyAwk': 1, 'AssemblyTeX': 1, 'AssemblySmalltalk': 1, 'AssemblyFortran': 1, 'AssemblyTSQL': 1, 'AssemblyKotlin': 1, 'AssemblyProlog': 1, 'AssemblyB+NULL': 3, 'AssemblyTcl': 1, 'AssemblyDIGITAL Command Language': 1, 'AssemblySQLPL': 1, 'AssemblyGLSL': 1, 'AssemblyXML': 1, 'AssemblyANTLR': 1, 'AssemblyThrift': 1, 'AssemblyLex': 1, 'AssemblyScala': 1, 'AssemblyD': 1, 'AssemblyHaskell': 1, 'AssemblyIDL': 1, 'AssemblyYacc': 1, 'CMakeTeX': 1, 'CMakeSmalltalk': 1, 'CMakeVim script': 1, 'CMakeTSQL': 1, 'CMakeASP': 2, 'CMakeXSLT': 2, 'CMakeB+NULL': 3, 'CMakeDart': 1, 'CMakeTcl': 2, 'CMakeDIGITAL Command Language': 2, 'CMakeSQLPL': 1, 'CMakeGLSL': 2, 'CMakeOpenEdge ABL': 1, 'CMakeGAP': 1, 'CMakeGherkin': 1, 'CMakeBoo': 1, 'CMake1C Enterprise': 1, 'CudaAwk': 1, 'CudaTeX': 1, 'CudaVim script': 1, 'CudaM': 1, 'CudaProlog': 1, 'CudaB+NULL': 1, 'OCamlSmalltalk': 1, 'OCamlAppleScript': 1, 'OCamlKotlin': 1, 'OCamlProlog': 1, 'OCamlB+NULL': 2, 'OCamlXML': 1, 'OCamlANTLR': 1, 'OCamlThrift': 1, 'OCamlLex': 1, 'OCamlScala': 1, 'OCamlD': 1, 'OCamlHaskell': 1, 'OCamlIDL': 1, 'OCamlYacc': 1, 'AwkTeX': 1, 'AwkVim script': 1, 'AwkFortran': 1, 'AwkM': 1, 'AwkAppleScript': 1, 'AwkProlog': 1, 'AwkB+NULL': 3, 'AwkGnuplot': 1, 'AwkErlang': 1, 'TeXVim script': 1, 'TeXM': 1, 'TeXTSQL': 1, 'TeXProlog': 1, 'TeXB+NULL': 4, 'TeXTcl': 1, 'TeXDIGITAL Command Language': 1, 'TeXSQLPL': 1, 'TeXGLSL': 1, 'TeXOpenEdge ABL': 1, 'TeXMetal': 1, 'TeXCrystal': 1, 'SmalltalkASP': 1, 'SmalltalkXSLT': 1, 'SmalltalkKotlin': 1, 'SmalltalkProlog': 1, 'SmalltalkB+NULL': 2, 'SmalltalkTcl': 1, 'SmalltalkGLSL': 1, 'SmalltalkXML': 1, 'SmalltalkANTLR': 1, 'SmalltalkThrift': 1, 'SmalltalkLex': 1, 'SmalltalkScala': 1, 'SmalltalkD': 1, 'SmalltalkHaskell': 1, 'SmalltalkIDL': 1, 'SmalltalkYacc': 1, 'SmalltalkGAP': 1, 'SmalltalkGherkin': 1, 'SmalltalkBoo': 1, 'Vim scriptM': 1, 'Vim scriptAppleScript': 1, 'Vim scriptASP': 1, 'Vim scriptXSLT': 1, 'Vim scriptProlog': 1, 'Vim scriptB+NULL': 5, 'Vim scriptDart': 1, 'Vim scriptDIGITAL Command Language': 1, 'Vim scriptOpenEdge ABL': 1, 'Vim scriptHCL': 1, 'Vim script1C Enterprise': 1, 'FortranB+NULL': 1, 'MProlog': 1, 'MB+NULL': 1, 'AppleScriptB+NULL': 3, 'AppleScriptGnuplot': 1, 'AppleScriptErlang': 1, 'PascalB+NULL': 1, 'PascalHCL': 1, 'PascalPLSQL': 1, 'PascalPuppet': 1, 'VueB+NULL': 2, 'TSQLB+NULL': 1, 'TSQLTcl': 1, 'TSQLDIGITAL Command Language': 1, 'TSQLSQLPL': 1, 'TSQLGLSL': 1, 'ASPXSLT': 2, 'ASPB+NULL': 3, 'ASPDart': 2, 'ASPTcl': 1, 'ASPDIGITAL Command Language': 1, 'ASPGLSL': 1, 'ASPOpenEdge ABL': 1, 'ASPScala': 1, 'ASPNginx': 1, 'ASPGAP': 1, 'ASPGherkin': 1, 'ASPBoo': 1, 'ASP1C Enterprise': 1, 'XSLTB+NULL': 3, 'XSLTDart': 1, 'XSLTProtocol Buffer': 1, 'XSLTTcl': 1, 'XSLTDIGITAL Command Language': 1, 'XSLTGLSL': 1, 'XSLTOpenEdge ABL': 1, 'XSLTNginx': 1, 'XSLTCOBOL': 1, 'XSLTSaltStack': 1, 'XSLTGAP': 1, 'XSLTGherkin': 1, 'XSLTBoo': 1, 'XSLT1C Enterprise': 1, 'KotlinProlog': 1, 'KotlinB+NULL': 2, 'KotlinDart': 1, 'KotlinXML': 1, 'KotlinANTLR': 1, 'KotlinThrift': 1, 'KotlinLex': 1, 'KotlinScala': 1, 'KotlinD': 1, 'KotlinHaskell': 1, 'KotlinIDL': 1, 'KotlinYacc': 1, 'PrologB+NULL': 2, 'PrologXML': 1, 'PrologANTLR': 1, 'PrologThrift': 1, 'PrologLex': 1, 'PrologScala': 1, 'PrologD': 1, 'PrologHaskell': 1, 'PrologIDL': 1, 'PrologYacc': 1, 'B+NULLDart': 4, 'B+NULLProtocol Buffer': 3, 'B+NULLTcl': 2, 'B+NULLDIGITAL Command Language': 2, 'B+NULLSQLPL': 1, 'B+NULLGLSL': 2, 'B+NULLOpenEdge ABL': 2, 'B+NULLMetal': 1, 'B+NULLPostScript': 1, 'B+NULLHCL': 3, 'B+NULLXML': 1, 'B+NULLANTLR': 1, 'B+NULLThrift': 1, 'B+NULLLex': 1, 'B+NULLScala': 2, 'B+NULLD': 1, 'B+NULLHaskell': 1, 'B+NULLIDL': 1, 'B+NULLYacc': 1, 'B+NULLNginx': 2, 'B+NULLCOBOL': 1, 'B+NULLSaltStack': 1, 'B+NULLCrystal': 1, 'B+NULLPLSQL': 1, 'B+NULLPuppet': 1, 'B+NULLGAP': 1, 'B+NULLGherkin': 1, 'B+NULLBoo': 1, 'B+NULLGnuplot': 1, 'B+NULLErlang': 1, 'B+NULL1C Enterprise': 1, 'DartProtocol Buffer': 1, 'DartDIGITAL Command Language': 1, 'DartOpenEdge ABL': 1, 'DartScala': 1, 'DartNginx': 1, 'Dart1C Enterprise': 1, 'Protocol BufferNginx': 1, 'Protocol BufferCOBOL': 1, 'Protocol BufferSaltStack': 1, 'TclDIGITAL Command Language': 1, 'TclSQLPL': 1, 'TclGLSL': 2, 'TclGAP': 1, 'TclGherkin': 1, 'TclBoo': 1, 'DIGITAL Command LanguageSQLPL': 1, 'DIGITAL Command LanguageGLSL': 1, 'DIGITAL Command LanguageOpenEdge ABL': 1, 'DIGITAL Command Language1C Enterprise': 1, 'SQLPLGLSL': 1, 'GLSLGAP': 1, 'GLSLGherkin': 1, 'GLSLBoo': 1, 'OpenEdge ABLMetal': 1, 'OpenEdge ABL1C Enterprise': 1, 'HCLPLSQL': 1, 'HCLPuppet': 1, 'XMLANTLR': 1, 'XMLThrift': 1, 'XMLLex': 1, 'XMLScala': 1, 'XMLD': 1, 'XMLHaskell': 1, 'XMLIDL': 1, 'XMLYacc': 1, 'ANTLRThrift': 1, 'ANTLRLex': 1, 'ANTLRScala': 1, 'ANTLRD': 1, 'ANTLRHaskell': 1, 'ANTLRIDL': 1, 'ANTLRYacc': 1, 'ThriftLex': 1, 'ThriftScala': 1, 'ThriftD': 1, 'ThriftHaskell': 1, 'ThriftIDL': 1, 'ThriftYacc': 1, 'LexScala': 1, 'LexD': 1, 'LexHaskell': 1, 'LexIDL': 1, 'LexYacc': 1, 'ScalaD': 1, 'ScalaHaskell': 1, 'ScalaIDL': 1, 'ScalaYacc': 1, 'ScalaNginx': 1, 'DHaskell': 1, 'DIDL': 1, 'DYacc': 1, 'HaskellIDL': 1, 'HaskellYacc': 1, 'IDLYacc': 1, 'NginxCOBOL': 1, 'NginxSaltStack': 1, 'COBOLSaltStack': 1, 'PLSQLPuppet': 1, 'GAPGherkin': 1, 'GAPBoo': 1, 'GherkinBoo': 1, 'GnuplotErlang': 1}


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
    # repoLangToGml()
    # devLangToGml()
    repoLangOneModeToGml()
    devLangOneModeToGml()