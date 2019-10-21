import requests
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
            cursor.execute(query, args)
            return cursor.fetchall()

def reposToMysql():

    sqlconn = MySqlConn()
    devs = sqlconn.run('SELECT username FROM dev;')
    for dev in devs:
        username = dev[0]
        url = 'https://api.github.com/users/'+username+'/repos'

        r = requests.get(url).json()


        for i in range(len(r)):
            reponame = r[i]['full_name']
            url = 'https://github.com/' + reponame
            sqlconn = MySqlConn()
            devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(username))[0][0]
            try:
                repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
                sqlconn.run('INSERT INTO contributes (devid, repoid) VALUES (%d, %d);' %(devid, repoid))
            except:
                sqlconn.run('INSERT INTO repo (reponame, url) VALUES ("%s", "%s");' %(reponame, url))
                repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
                sqlconn.run('INSERT INTO contributes (devid, repoid) VALUES (%d, %d);' %(devid, repoid))
            sqlconn.connection.commit()
            sqlconn.connection.close()
    return
reposToMysql()