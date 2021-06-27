from datetime import datetime
from sqlite3 import connect, OperationalError
from kivy.logger import Logger
from kivy.utils import platform


class MyDb:
    def __init__(self, dbName=''):
        if not dbName:
            dbName = '../database.db' if platform == 'android' else 'database.db'

        self.conn = connect(dbName)
        dest = connect(':memory:')
        self.conn.backup(dest)

    def create(self):
        c = self.conn.cursor()
        with self.conn:
            try:
                c.execute("""create table proxys (
                    time datetime,
                    protocol text,
                    ip text,
                    size real,
                    getfiletime text,
                    speed integer,
                    top3c integer
                    )""")
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

            try:
                c.execute("""create table proxysHistory (
                    time datetime,
                    protocol text,
                    ip text,
                    size real,
                    getfiletime text,
                    speed integer,
                    top3c integer,
                    mirror text
                    )""")
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

            try:
                c.execute("""create table proxysInx (
                    proxysInx datetime,
                    totalScan integer
                    )""")
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

            try:
                c.execute('''create table configs (
                    themeMode text,
                    miInx integer,
                    proxysInx datetime,
                    timeoutD integer,
                    fileSize integer,
                    autoKill integer,
                    autoKillMode bit,
                    openNo text
                    )''')
                c.execute(
                    "INSERT INTO configs \
                        (themeMode, miInx, timeoutD, fileSize, \
                            autoKill, autoKillMode, openNo) \
                            VALUES ('Dark',0, 5, 1062124, 50000, 0, '400')"
                )
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

            try:
                self.createMirror()
                c.execute(
                    "INSERT INTO mirrors VALUES ('http://bd.archive.ubuntu.com/ubuntu/indices/override.oneiric.universe')")
                c.execute(
                    "INSERT INTO mirrors VALUES ('http://provo.speed.googlefiber.net:3004/download?size=1048576')")
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

    def createMirror(self):
        c = self.conn.cursor()
        with self.conn:
            c.execute("create table mirrors (mirror text)")

    def getAllConfigs(self):
        c = self.conn.cursor()
        with self.conn:
            c.execute("SELECT * FROM 'configs'")
            configs = c.fetchall()
        return configs

    def getAllMirrors(self):
        c = self.conn.cursor()
        with self.conn:
            c.execute("SELECT * FROM 'mirrors'")
            mirrors = c.fetchall()
        return mirrors

    def getProxysInx(self, name='proxysInx'):
        c = self.conn.cursor()
        with self.conn:
            c.execute(f"SELECT {name} FROM 'proxysInx'")
            proxysInx = c.fetchall()
        return proxysInx

    def getProxysInxTS(self, time):
        c = self.conn.cursor()
        with self.conn:
            c.execute(
                f"SELECT totalScan FROM 'proxysInx' WHERE proxysInx=?", [time])
            totalScan = c.fetchone()
        return totalScan

    def getConfig(self, name):
        c = self.conn.cursor()
        with self.conn:
            c.execute(f"SELECT {name} FROM 'configs'")
            config = c.fetchone()
        return config

    def getAllCurrentProxys(self, time):
        c = self.conn.cursor()
        with self.conn:
            c.execute(
                "SELECT ip, size, getfiletime, speed, protocol, time, top3c FROM 'proxys' WHERE time=? ORDER BY speed DESC", [time])
            scan_list = c.fetchall()
        return scan_list

    def getAllProxyScan(self, addr):
        c = self.conn.cursor()
        with self.conn:
            c.execute(
                "SELECT ip, size, getfiletime, speed, protocol, time, top3c, mirror FROM 'proxysHistory' WHERE ip=? ORDER BY time DESC", [addr])
            scan_list = c.fetchall()
        return scan_list

    def updateThemeMode(self, name):
        c = self.conn.cursor()
        with self.conn:
            c.execute("UPDATE 'configs' SET themeMode=?", [name])

    def updateScanList(self, l, afterTime):
        c = self.conn.cursor()
        with self.conn:
            try:
                for p in l:
                    c.execute("UPDATE proxys SET size=?, getfiletime=?, speed=?, top3c=? WHERE ip=? AND time=?",
                              (p['SIZE'], p['TIME'], p['SPEED'], p['top3c'], p['IP'], afterTime))
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

    def updateConfig(self, key, value):
        c = self.conn.cursor()
        with self.conn:
            c.execute(f"UPDATE 'configs' SET {key}=?", [value])

    def updateProxysInx(self, new, old):
        c = self.conn.cursor()
        with self.conn:
            c.execute(
                "UPDATE 'proxysInx' SET proxysInx=?, totalScan=totalScan+1 WHERE proxysInx=?", (new, old))

    def updateProxys(self, new, old):
        c = self.conn.cursor()
        with self.conn:
            c.execute(
                "UPDATE 'proxys' SET time=?, size=NULL, getfiletime=NULL, speed=NULL WHERE time=?", (new, old))

    def inputProxyHistory(self, dict, protocol, mirror):
        c = self.conn.cursor()
        with self.conn:
            try:
                c.execute(
                    'INSERT INTO proxysHistory \
                    (time, ip, protocol, top3c, size, \
                        getfiletime, speed, mirror) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        datetime.now(),
                        dict['IP'],
                        protocol,
                        dict['top3c'],
                        dict['SIZE'],
                        dict['TIME'],
                        dict['SPEED'],
                        mirror))
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")

    def createProxysList(self, proxys, protocol, IndexTime):
        c = self.conn.cursor()
        with self.conn:
            for l in proxys:
                if not l:
                    continue
                try:
                    c.execute(
                        'INSERT INTO proxys (time, ip, protocol, top3c) VALUES (?, ?, ?, 0)', (IndexTime, l, protocol))
                except OperationalError as e:
                    Logger.info(f"Sqlite3 : {e}")

            self.updateConfig('proxysInx', IndexTime)
            c.execute(
                "INSERT INTO proxysInx (proxysInx, totalScan) VALUES (?, ?)", (IndexTime, 0))

    def drop(self, name):
        c = self.conn.cursor()
        with self.conn:
            c.execute(f"DROP TABLE '{name}'")

    def inputeMirror(self, l):
        self.drop('mirrors')
        self.createMirror()

        c = self.conn.cursor()
        with self.conn:
            for line in l:
                if not line == '':
                    c.execute("INSERT INTO mirrors VALUES (?)", [line.strip()])

        self.updateConfig('miInx', 0)

    def deletePoint(self, table, column, point):
        c = self.conn.cursor()
        with self.conn:
            try:
                com = f"DELETE FROM {table} WHERE {column} = (?)"
                c.execute(com, [point.strip()])
                return True
            except OperationalError as e:
                Logger.info(f"Sqlite3 : {e}")
        return False
