import requests
import pymysql


class MySqlConn:
    def __init__(self):
        connection_options = {
            'host': 'localhost',
            'user': 'chends',
            'password': '8888',
            'database': 'gitreposdevs'}
        self.connection = pymysql.connect(**connection_options)

    def run(self, query, args=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchall()


def devsToMysql():

    sqlconn = MySqlConn()
    repos = sqlconn.run('SELECT reponame FROM repo;')
    for repo in repos:
        reponame = repo[0]
        url = 'http://api.github.com/repos/'+ reponame + '/contributors?client_id=27b6c06c22f39c8b4762&client_secret=25eb0aaac1ca1e5a078a5eddd8971b8ed80627e5'
        r = requests.get(url).json()
        for i in range(len(r)):
            # reponame = r[i]['full_name']
            devname = r[i]['login']
            sqlconn = MySqlConn()
            repoid = sqlconn.run('SELECT id FROM repo WHERE reponame="%s";' %(reponame))[0][0]
            try:
                devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(devname))[0][0]
                sqlconn.run('INSERT INTO contributes (devid, repoid) VALUES (%d, %d);' %(devid, repoid))
            except:
                sqlconn.run('INSERT INTO dev (username) VALUES ("%s");' %(devname))
                devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(devname))[0][0]
                sqlconn.run('INSERT INTO contributes (devid, repoid) VALUES (%d, %d);' %(devid, repoid))
            sqlconn.connection.commit()
            sqlconn.connection.close()
    return

devsToMysql()
