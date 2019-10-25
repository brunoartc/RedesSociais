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


def toGml():
    tmp = 'graph [\n  directed 1\n'
    sqlconn = MySqlConn()
    devs = sqlconn.run('SELECT username FROM dev;')
    usernames_id = []
    # devids = []
    # Creating nodes for devs
    for dev in devs:
        username = dev[0]
        devid = sqlconn.run('SELECT id FROM dev WHERE username="%s";' %(username))[0][0]
        usernames_id.append([devid, username])
        # usernames.append(username)
        tmp += '  node [\n    id "'+ username +'"\n  ]\n'
    # Creating nodes for repos
    repos = sqlconn.run('SELECT reponame FROM repo;')
    for reponame in repos:
        reponame = reponame[0]
        tmp += '  node [\n    id "'+str(reponame)+'"\n  ]\n'
    for name_id in usernames_id:
        devrepos = sqlconn.run('SELECT repoid FROM contributes WHERE devid=%d;' %(name_id[0]))
        for repoid in devrepos:
            repoid = repoid[0]
            reponame = sqlconn.run('SELECT reponame FROM repo WHERE id="%s";' %(repoid))[0][0]
            tmp += '  edge [\n    source "'+ name_id[1] +'"\n    target "'+str(reponame)+'"\n  ]\n'


    sqlconn.connection.close()

    tmp += ']'
    filename = 'data/devs_repos.gml'
    with open(filename, 'w') as f:
        f.write(tmp)

toGml()