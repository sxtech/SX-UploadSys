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
from sqlitedb import U_Sqlite
from iniconf import Img_Ini
from helpfunc import HelpFunc
from disk import DiskState
from ntp import NtpClient
import pythoncom
import uploaddata
from DBUtils.PooledDB import PooledDB
from DBUtils.PersistentDB import PersistentDB
#from singleinstance import singleinstance

logger = logging.getLogger('root')

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


class DataClient:
    #��ʼ����
    def __init__(self,trigger=0):
        logger.info('Logon System!')
        self.imgIni     = Img_Ini()             #�����ļ�ʵ��
        self.imgfileini = self.imgIni.getImgFileConf()
        self.mysqlini   = self.imgIni.getMysqldbConf()
        self.ntpini     = self.imgIni.getNTP()

        self.ntpip = self.ntpini['ip']    #ntp����IP
        
        self.hf = HelpFunc()               #����������ʵ��

        self.loginMysql()

        self.loginCount=0
        
        pythoncom.CoInitialize() #���wmi����
        self.dis = DiskState()

        #��ʼ��ʱ��״̬��Ϣ
        self.sqlite = U_Sqlite()
        self.sqlite.createTable()
        s = self.sqlite.getUploadsys()
        
        gl.STATED['year']  = s[1]
        gl.STATED['month'] = s[2]
        gl.STATED['day']   = s[3]
        gl.STATED['hour']  = s[4]
        gl.TRIGGER.emit("#%s��%s��%s��%sʱ"%(gl.STATED['year'],gl.STATED['month'],gl.STATED['day'],gl.STATED['hour']))

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
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,self.hf.getTime()+'Start to login mysql...'))
            mysqlPool(mysqlini['host'],mysqlini['user'],mysqlini['passwd'],3306,mysqlini['mincached'],mysqlini['maxcached'],mysqlini['maxshared'],mysqlini['maxconnections'],mysqlini['maxusage'])
            gl.MYSQLLOGIN = True
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,self.hf.getTime()+'Login mysql success!'))
            logger.info('Login mysql success!')
            self.loginCount = 0
        except Exception,e:
            gl.MYSQLLOGIN = False
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_red,self.hf.getTime()+str(e)))
            self.loginCount = 1
        
    def main(self):
        hourflag = gl.STATED['hour']
        n = threading.Thread(target=self.ntpThread)
        n.start()
        while 1:
            #print self.dis.getSize()
            
            #�˳�����
            if gl.QTFLAG == False and gl.THREADDICT != {}:
                gl.DCFLAG = False  #�˳����
                break

            #���ʱ���¼�б仯д��sqlite
            if hourflag != gl.STATED['hour']:
                self.sqlite.updateUploadsys(gl.STATED['year'],gl.STATED['month'],gl.STATED['day'],gl.STATED['hour'])
                gl.TRIGGER.emit("#%s��%s��%s��%sʱ"%(gl.STATED['year'],gl.STATED['month'],gl.STATED['day'],gl.STATED['hour']))

            if gl.QTFLAG == False:    
                if gl.THREADDICT == {}:
                    gl.DCFLAG = False  #�˳���ʶ
                    break
            elif self.loginCount > 0:
                if self.loginCount >= 15:
                    self.loginMysql()
                else:
                    self.loginCount += 1
            elif gl.MYSQLLOGIN:
                s = self.getUploadTime(gl.STATED['year'],gl.STATED['month'],gl.STATED['day'],gl.STATED['hour'])
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
                self.loginCount+=1

            time.sleep(5)
            
        logger.warning('Logout System!')
        gl.DCFLAG = False  #�˳����

    #ntpʱ��ͬ���߳�
    def ntpThread(self):
        ntp = NtpClient(self.ntpip)
        count = 2*60*60
        while 1:
            try:
                #�˳�����
                if gl.QTFLAG == False:
                    gl.DCFLAG = False  #�˳����
                    break
                
                if count >= 2*60*60:
                    ts = ntp.setTime()
                    gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,self.hf.getTime()+'ʱ����%s��%sͬ���ɹ�'%(time.strftime('%Y-%m-%d %X', time.localtime(ts)),self.ntpip)))
                    count = 0
                else:
                    count += 1
            except Exception,e:
                logger.error(str(e))
                gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_red,self.hf.getTime()+'ϵͳ����%s����ͬ������'%self.ntpip))
                count = 0
            time.sleep(1)
        del ntp

    #����ʱ���ȡʱ�����Դ����߳�
    def getUploadTime(self,year,month,day,hour):
        now   = datetime.datetime.now()                 #��ǰʱ��
        after = now + datetime.timedelta(minutes = 5)   #5���Ӻ�ʱ��
        
        if gl.THREADDICT.get((now.year,now.month,now.day,now.hour),-1)==-1:
            return datetime.date(now.year,now.month,now.day),now.hour
        elif after.hour != now.hour and gl.THREADDICT.get((after.year,after.month,after.day,after.hour),-1)==-1:
            return datetime.date(after.year,after.month,after.day),after.hour
        elif datetime.datetime(year,month,day,hour)<now and gl.THREADDICT.get((year,month,day,hour),-1)==-1:
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
