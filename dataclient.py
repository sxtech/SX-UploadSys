# -*- coding: cp936 -*-
import time,datetime,os,glob,sys
import MySQLdb
import sqlite3
import logging
import logging.handlers
import cPickle
import ConfigParser
import threading
import gl
from sqlitedb import Sqlite
from iniconf import ImgIni
from helpfunc import HelpFunc
import uploaddata
from DBUtils.PooledDB import PooledDB
from DBUtils.PersistentDB import PersistentDB
#from singleinstance import singleinstance


def getTime():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

#mysql�̳߳�
def mysqlPool(h,u,ps,pt,minc=5,maxc=20,maxs=10,maxcon=100,maxu=1000):
    gl.mysqlpool = PooledDB(
        MySQLdb,
        host    = h,
        user    = u,
        passwd  = ps,
        db      = "img_center",
        charset = "gbk",
        mincached = minc,        #����ʱ�����Ŀ���������
        maxcached = maxc,        #���ӳ���������������
        maxshared = maxs,        #���ӳ����ɹ�����������
        maxconnections = maxcon, #���������������
        maxusage  = maxu)

#sqlite�̳߳�
def sqlitePool(db="uploadsys.db",maxu=1000):
    gl.sqlitepool = PersistentDB(
        sqlite3,
        maxusage = maxu,
        database = db)

def ipToBigint(ipaddr):
    ipStrs = ipaddr.split(".")

    return str(int(ipStrs[3]) + int(ipStrs[2])*256 + int(ipStrs[1])*256*256 + int(ipStrs[0])*256*256*256) 


class DataClient:
    #��ʼ����
    def __init__(self,trigger=0):      
        self.imgIni     = ImgIni()             #�����ļ�ʵ��
        self.imgfileini = self.imgIni.getImgFileConf()
        self.mysqlini   = self.imgIni.getMysqldbConf()

        self.hf = HelpFunc()               #����������ʵ��

        self.loginMysql()

        #sqlitePool("uploadsys.db")

        #��ʼ��ʱ��״̬��Ϣ
        self.sqlite = Sqlite()
        self.sqlite.createTable()
        state = self.sqlite.getUploadsys()
        gl.STATE['year']  = state[1]
        gl.STATE['month'] = state[2]
        gl.STATE['day']   = state[3]
        gl.STATE['hour']  = state[4]

        gl.LOCALIP = self.hf.ipToBigint(self.imgfileini['ip'])
        gl.IMGPATH = self.imgfileini['imgpath']
        gl.KAKOU   = os.listdir(gl.IMGPATH)

    #��������
    def __del__(self):
        del self.imgIni
        del self.sqlite
        del self.hf

    #��¼mysql
    def loginMysql(self):
        mysqlini = self.mysqlini
        try:
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,getTime()+'Start to login mysql...'))
            mysqlPool(mysqlini['host'],mysqlini['user'],mysqlini['passwd'],3306,mysqlini['mincached'],mysqlini['maxcached'],mysqlini['maxshared'],mysqlini['maxconnections'],mysqlini['maxusage'])
            gl.MYSQLLOGIN = True
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,getTime()+'Login mysql success!'))
            logging.info('Login mysql success!')
        except Exception,e:
            gl.MYSQLLOGIN = False
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_red,getTime()+str(e)))
            time.sleep(15)
        
    def main(self):
        count = 0
        hourflag = gl.STATE['hour']
        while 1:
            if count >20 or count == 0:
                print "current has %d threads" % (threading.activeCount() - 2)
                for item in threading.enumerate():
                    print 'item',item
                print gl.THREADDICT
                print gl.STATE
                count = 1

            #�˳�����
            if gl.QTFLAG == False and gl.THREADDICT != {}:
                gl.DCFLAG = False  #�˳����
                break

            #���ʱ���¼�б仯д��sqlite
            if hourflag != gl.STATE['hour']:
                self.sqlite.updateUploadsys(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour'])
            
            if gl.MYSQLLOGIN:
                s = self.getUploadTime(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour'])
                if s != None:
                    # �����߳�
                    try:
                        gl.THREADDICT[(s[0].year,s[0].month,s[0].day,s[1])] = datetime.datetime.now()
                        t = uploaddata.UploadData(datetime.date(s[0].year,s[0].month,s[0].day),s[1])
                        t.setDaemon(False)
                        t.start()
                    except:
                        pass
            elif gl.THREADDICT != {}:
                pass
            else:
                self.loginMysql()
            count +=1

            time.sleep(1)
            
        gl.DCFLAG = False  #�˳����

    #����ʱ���ȡʱ�����Դ����߳�
    def getUploadTime(self,year,month,day,hour):
        now   = datetime.datetime.now()                 #��ǰʱ��
        after = now + datetime.timedelta(minutes = 5)   #5���Ӻ�ʱ��
        
        if gl.THREADDICT.get((now.year,now.month,now.day,now.hour),-1)==-1:
            return datetime.date(now.year,now.month,now.day),now.hour
        elif after.hour != now.hour and gl.THREADDICT.get((after.year,after.month,after.day,after.hour),-1)==-1:
            return datetime.date(after.year,after.month,after.day),after.hour
        elif gl.THREADDICT.get((year,month,day,hour),-1)==-1:
            return datetime.date(year,month,day),hour
        else:
            return None

            
if __name__ == "__main__":
    try:
        dc = DataClient()
        dc.main()

        
    except MySQLdb.Error,e:
        print e
    else:
        pass
