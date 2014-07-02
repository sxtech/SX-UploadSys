# -*- coding: cp936 -*-
import threading
import gl
import glob
import MySQLdb
import logging
import logging.handlers
import os,datetime,time,sys
import ConfigParser
from iniconf import ImgIni,PlateIni
from mysqldb import ImgMysql
from helpfunc import HelpFunc

def mysqlPool(h,u,ps,pt,minc=5,maxc=20,maxs=10,maxcon=100,maxu=1000):
    gl.mysqlpool = PooledDB(
        MySQLdb,
        host = 'localhost',
        user = 'root',
        passwd = '',
        db = "img_center",
        charset = "gbk",
        mincached = minc,        #启动时开启的空连接数量
        maxcached = maxc,        #连接池最大可用连接数量
        maxshared = maxs,        #连接池最大可共享连接数量
        maxconnections = maxcon, #最大允许连接数量
        maxusage = maxu)

class UploadData(threading.Thread):
    #初始函数
    def __init__(self,date,hour):
        try:
            self.direction = {'0':'进城','1':'出城','2':'由东往西','3':'由南往北','4':'由西往东','5':'由北往南'}
            self.hour_dict = {0:'00',1:'01',2:'02',3:'03',4:'04',5:'05',6:'06',7:'07',
                         8:'08',9:'09',10:'10',11:'11',12:'12',13:'13',14:'14',15:'15',
                         16:'16',17:'17',18:'18',19:'19',20:'20',21:'21',22:'22',23:'23'}

            self.mysql   = ImgMysql()                #mysql操作类实例
            self.plaIni  = PlateIni()                #车辆信息配置文件
            self.imgIni  = ImgIni()                  #配置文件类实例
            self.hf      = HelpFunc()                #辅助函数类实例
            
            self.strdate = date.strftime('%Y%m%d')   #字符串日期
            self.date    = date                      #日期
            self.hour    = hour                      #小时
            threadname   = self.strdate+self.hour_dict.get(hour,'00')
            threading.Thread.__init__(self,name=threadname)

            logging.info('开始线程'+self.getName())
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_royalblue,self.hf.getTime()+'开始线程'+self.getName()))

            gl.THREADDICT[(self.date.year,self.date.month,self.date.day,self.hour)]=datetime.datetime.now()

            #结束时间标记
            self.endtime  = datetime.datetime(date.year,date.month,date.day,hour)+datetime.timedelta(minutes = 65)
            self.imgset   = set()                     #ini文件路径集合
            self.faultset = set()                     #ini错误文件集合
            self.ip_dict  = {}                        #IP字典
            
        except Exception,e:
            print e

    def run(self):
        try:
            self.getHistoryData()

            while True:
                print self.getName()
                self.mysql.getVersion()
                difset = self.getNewData() - self.imgset
                
                #先添加报错的车辆信息集合
                if self.faultset != set():
                    time.sleep(0.5)
                    self.addIndex(self.faultset)
                    self.faultset = set()
                    
                #添加新添加的车辆信息集合
                if difset != set():
                    self.addIndex(difset)
                    self.imgset = self.imgset|difset      #并集
                    
                #超过当前时间5分钟的时候退出
                if datetime.datetime.now() > self.endtime and self.faultset==set():
                    break

                #退出标记
                if gl.QTFLAG == False:
                    break
                
                time.sleep(1)
        except MySQLdb.Error,e:
            if gl.MYSQLLOGIN:
                gl.MYSQLLOGIN = False
                logging.error(str(e))
                gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_red,self.hf.getTime()+str(e)))
        else:
            if self.date.year == gl.STATE['year'] and self.date.month == gl.STATE['month'] and self.date.day == gl.STATE['day'] and self.hour == gl.STATE['hour']:
                nexttime = datetime.datetime(self.date.year,self.date.month,self.date.day,self.hour) + datetime.timedelta(hours = 1)
                gl.STATE['year']  = nexttime.year
                gl.STATE['month'] = nexttime.month
                gl.STATE['day']   = nexttime.day
                gl.STATE['hour']  = nexttime.hour
                #self.sqlite.updateUploadsys(gl.STATE['year'],gl.STATE['month'],gl.STATE['day'],gl.STATE['hour'])
            time.sleep(1)
        finally:
            try:
                logging.info('退出线程'+self.getName())
                gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_brown,self.hf.getTime()+'退出线程'+self.getName()))

                del self.mysql
                del self.imgIni
                del self.plaIni
                del self.hf
                del gl.THREADDICT[(self.date.year,self.date.month,self.date.day,self.hour)]
            except Exception,e:
                print e
        
    #获取历史车辆信息
    def getHistoryData(self):
        imgfile = self.mysql.getImgfileByTime(str(self.date),self.hour,gl.LOCALIP)
        for i in imgfile:
            self.imgset.add(i['imgfile'].encode(gl.CHARSET)[:-4]+'.ini')

    #获取最新车辆信息
    def getNewData(self):
        data_set = set()
        try:
            for i in gl.KAKOU:
                path = os.path.join(gl.IMGPATH,i,self.strdate,self.hour_dict.get(self.hour,'00'))
                try:
                    os.chdir(path)
                    f = glob.glob('*\*.ini')
                    for j in f:
                        data_set.add(os.path.join(i,self.strdate,self.hour_dict.get(self.hour,'00'),j))
                except Exception,e:
                    pass
        except Exception,e:
            raise
        finally:
            return data_set

    #添加新的车辆消息到数据库
    def addIndex(self,_set):
        time = datetime.datetime.now()
        values = []     #车辆信息列表，用于批量添加到mysql
        cip = 0

        for i in _set:
            try:
                plateinfo = self.plaIni.getPlateInfo(os.path.join(gl.IMGPATH,i))
                if plateinfo['carspeed'] > plateinfo['limitspeed']:
                    overspeed = 100.0*(plateinfo['carspeed']/plateinfo['limitspeed']-1)
                else:
                    overspeed = 0.0
                imgpath=''
                cip = self.ip_dict.get(plateinfo['cameraip'],-1)
                if cip == -1:
                    cip = self.hf.ipToBigint(plateinfo['cameraip'])
                    self.ip_dict[plateinfo['cameraip']] = cip
                    
                values.append((self.date,self.hour,gl.LOCALIP,time,i[:-4]+'.jpg',imgpath,
                               plateinfo['deviceid'],plateinfo['roadname'],plateinfo['roadid'],plateinfo['channelname'],
                               plateinfo['channelid'],plateinfo['passdatetime'],plateinfo['datetime'],plateinfo['platecode'],
                               plateinfo['platecolor'],plateinfo['platetype'],plateinfo['vehiclelen'],plateinfo['vehiclecolor'],
                               plateinfo['vehiclecoltype'],plateinfo['speed'],plateinfo['carspeed'],plateinfo['limitspeed'],
                               plateinfo['speedd'],plateinfo['speedx'],overspeed,cip,plateinfo['directionid'],plateinfo['channeltype']))
            except ConfigParser.Error,e:
                print e
                self.faultset.add(i)
        self.mysql.addIndex(values)
        self.showPlateInfo(values)

    #显示车辆信息
    def showPlateInfo(self,values):
        if datetime.datetime.now() > self.endtime:
            gl.TRIGGER.emit("<font %s>Upload %s history files</font>"%(gl.style_gray,len(values)))
        else:
            for i in values:
                carstr = '<table><tr style="font-family:arial;font-size:14px;color:blue"><td>[%s]<td><td width="100">%s</td><td width="40">%s</td><td width="160">%s</td><td width="70">%s</td><td width="40">%s车道</td></tr></table>'%(i[11],i[13],i[14],i[7],self.direction.get(i[26],'其他'),str(i[10]))
                gl.TRIGGER.emit("%s"%carstr)
                    
    def test(self,_set=set()):
        #_set = set([r'F:\\卡口\\imgs\\ImageFile\\测试卡口\1(出城)\20140113164737680_蓝牌粤B9041J.ini'])
        for i in _set:
            plateinfo = self.plaIni.getPlateInfo(os.path.join(gl.IMGPATH,i))
            print plateinfo


if __name__ == "__main__":
    import MySQLdb
    from DBUtils.PooledDB import PooledDB
    mysqlPool('localhost','root','',3306)
    print 'pool'
    time.sleep(10)

    gl.LOCALIP = self.hf.ipToBigint('127.0.0.1')
    gl.IMGPATH = "F:\\卡口\\imgs\\ImageFile\\"
    gl.KAKOU = os.listdir(gl.IMGPATH)
    
    ud = UploadData(datetime.date(2014,1,16),15).start()
    #ud = UploadData(datetime.date(2014,1,16),15)
    #ud.test()
