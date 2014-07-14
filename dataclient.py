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

#mysql线程池
def mysqlPool(h,u,ps,pt,minc=5,maxc=20,maxs=10,maxcon=100,maxu=1000):
    gl.mysqlpool = PooledDB(
        MySQLdb,
        host    = h,
        user    = u,
        passwd  = ps,
        db      = "img_center",
        charset = "gbk",
        mincached = minc,        #启动时开启的空连接数量
        maxcached = maxc,        #连接池最大可用连接数量
        maxshared = maxs,        #连接池最大可共享连接数量
        maxconnections = maxcon, #最大允许连接数量
        maxusage  = maxu)


class DataClient:
    #初始函数
    def __init__(self,trigger=0):      
        self.imgIni     = ImgIni()             #配置文件实例
        self.imgfileini = self.imgIni.getImgFileConf()
        self.mysqlini   = self.imgIni.getMysqldbConf()

        self.hf = HelpFunc()               #辅助函数类实例

        self.loginMysql()

        self.loginCount=0          #登录记数器

        #初始化时间状态信息
        self.sqlite = Sqlite()
        self.sqlite.createTable()
        state = self.sqlite.getUploadsys()
        gl.STATE['year']  = state[1]
        gl.STATE['month'] = state[2]
        gl.STATE['day']   = state[3]
        gl.STATE['hour']  = state[4]
        gl.TRIGGER.emit("#%s年%s月%s日%s时"%(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour']))

        gl.LOCALIP = self.hf.ipToBigint(self.imgfileini['ip'])
        gl.IMGPATH = self.imgfileini['imgpath']
        gl.KAKOU   = os.listdir(gl.IMGPATH)

    #析构函数
    def __del__(self):
        del self.imgIni
        del self.sqlite
        del self.hf

    #登录mysql
    def loginMysql(self):
        mysqlini = self.mysqlini
        try:
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,self.hf.getTime()+'Start to login mysql...'))
            mysqlPool(mysqlini['host'],mysqlini['user'],mysqlini['passwd'],3306,mysqlini['mincached'],mysqlini['maxcached'],mysqlini['maxshared'],mysqlini['maxconnections'],mysqlini['maxusage'])
            gl.MYSQLLOGIN = True
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_green,self.hf.getTime()+'Login mysql success!'))
            logging.info('Login mysql success!')
            self.loginCount = 0
        except Exception,e:
            gl.MYSQLLOGIN = False
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_red,self.hf.getTime()+str(e)))
            self.loginCount = 1
        
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

            #如何时间记录有变化写入sqlite
            if hourflag != gl.STATE['hour']:
                self.sqlite.updateUploadsys(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour'])
                gl.TRIGGER.emit("#%s年%s月%s日%s时"%(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour']))

            if gl.QTFLAG == False:    
                if gl.THREADDICT == {}:
                    gl.DCFLAG = False  #退出标记
                    break
            elif self.loginCount > 0:
                if self.loginCount >= 15:
                    self.loginMysql()
                else:
                    self.loginCount += 1
            elif gl.MYSQLLOGIN:
                s = self.getUploadTime(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour'])
                #print 'self.getUploadTime',s
                if s != None:
                    # 处理线程
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
            count +=1

            time.sleep(1)
            
        gl.DCFLAG = False  #退出标记

    #根据时间获取时间标记以创建线程
    def getUploadTime(self,year,month,day,hour):
        now   = datetime.datetime.now()                 #当前时间
        after = now + datetime.timedelta(minutes = 5)   #5分钟后时间
        
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
