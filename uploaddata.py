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
        mincached = minc,        #����ʱ�����Ŀ���������
        maxcached = maxc,        #���ӳ���������������
        maxshared = maxs,        #���ӳ����ɹ�����������
        maxconnections = maxcon, #���������������
        maxusage = maxu)

class UploadData(threading.Thread):
    #��ʼ����
    def __init__(self,date,hour):
        try:
            self.direction = {'0':'����','1':'����','2':'�ɶ�����','3':'��������','4':'��������','5':'�ɱ�����'}
            self.hour_dict = {0:'00',1:'01',2:'02',3:'03',4:'04',5:'05',6:'06',7:'07',
                         8:'08',9:'09',10:'10',11:'11',12:'12',13:'13',14:'14',15:'15',
                         16:'16',17:'17',18:'18',19:'19',20:'20',21:'21',22:'22',23:'23'}

            self.mysql   = ImgMysql()                #mysql������ʵ��
            self.plaIni  = PlateIni()                #������Ϣ�����ļ�
            self.imgIni  = ImgIni()                  #�����ļ���ʵ��
            self.hf      = HelpFunc()                #����������ʵ��
            
            self.strdate = date.strftime('%Y%m%d')   #�ַ�������
            self.date    = date                      #����
            self.hour    = hour                      #Сʱ
            threadname   = self.strdate+self.hour_dict.get(hour,'00')
            threading.Thread.__init__(self,name=threadname)

            logging.info('��ʼ�߳�'+self.getName())
            gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_royalblue,self.hf.getTime()+'��ʼ�߳�'+self.getName()))

            gl.THREADDICT[(self.date.year,self.date.month,self.date.day,self.hour)]=datetime.datetime.now()

            #����ʱ����
            self.endtime  = datetime.datetime(date.year,date.month,date.day,hour)+datetime.timedelta(minutes = 65)
            self.imgset   = set()                     #ini�ļ�·������
            self.faultset = set()                     #ini�����ļ�����
            self.ip_dict  = {}                        #IP�ֵ�
            
        except Exception,e:
            print e

    def run(self):
        try:
            self.getHistoryData()

            while True:
                print self.getName()
                self.mysql.getVersion()
                difset = self.getNewData() - self.imgset
                
                #����ӱ���ĳ�����Ϣ����
                if self.faultset != set():
                    time.sleep(0.5)
                    self.addIndex(self.faultset)
                    self.faultset = set()
                    
                #�������ӵĳ�����Ϣ����
                if difset != set():
                    self.addIndex(difset)
                    self.imgset = self.imgset|difset      #����
                    
                #������ǰʱ��5���ӵ�ʱ���˳�
                if datetime.datetime.now() > self.endtime and self.faultset==set():
                    break

                #�˳����
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
                logging.info('�˳��߳�'+self.getName())
                gl.TRIGGER.emit("<font %s>%s</font>"%(gl.style_brown,self.hf.getTime()+'�˳��߳�'+self.getName()))

                del self.mysql
                del self.imgIni
                del self.plaIni
                del self.hf
                del gl.THREADDICT[(self.date.year,self.date.month,self.date.day,self.hour)]
            except Exception,e:
                print e
        
    #��ȡ��ʷ������Ϣ
    def getHistoryData(self):
        imgfile = self.mysql.getImgfileByTime(str(self.date),self.hour,gl.LOCALIP)
        for i in imgfile:
            self.imgset.add(i['imgfile'].encode(gl.CHARSET)[:-4]+'.ini')

    #��ȡ���³�����Ϣ
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

    #����µĳ�����Ϣ�����ݿ�
    def addIndex(self,_set):
        time = datetime.datetime.now()
        values = []     #������Ϣ�б�����������ӵ�mysql
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

    #��ʾ������Ϣ
    def showPlateInfo(self,values):
        if datetime.datetime.now() > self.endtime:
            gl.TRIGGER.emit("<font %s>Upload %s history files</font>"%(gl.style_gray,len(values)))
        else:
            for i in values:
                carstr = '<table><tr style="font-family:arial;font-size:14px;color:blue"><td>[%s]<td><td width="100">%s</td><td width="40">%s</td><td width="160">%s</td><td width="70">%s</td><td width="40">%s����</td></tr></table>'%(i[11],i[13],i[14],i[7],self.direction.get(i[26],'����'),str(i[10]))
                gl.TRIGGER.emit("%s"%carstr)
                    
    def test(self,_set=set()):
        #_set = set([r'F:\\����\\imgs\\ImageFile\\���Կ���\1(����)\20140113164737680_������B9041J.ini'])
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
    gl.IMGPATH = "F:\\����\\imgs\\ImageFile\\"
    gl.KAKOU = os.listdir(gl.IMGPATH)
    
    ud = UploadData(datetime.date(2014,1,16),15).start()
    #ud = UploadData(datetime.date(2014,1,16),15)
    #ud.test()
