#-*- encoding: gb2312 -*-
import ConfigParser
import string, os, sys
import datetime
import time


class Img_Ini:
    def __init__(self,confpath = 'uploadsys.conf'):
        self.path = ''
        self.confpath = confpath
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(self.confpath)
    
    def getImgFileConf(self):
        imgfile = {}
        imgfile['imgpath'] = self.cf.get('IMGFILE','imgpath')
        imgfile['ip'] = self.cf.get('IMGFILE','ip')
        return imgfile

    def getMysqldbConf(self):
        mysqlconf = {}
        
        mysqlconf['host']   = self.cf.get('MYSQLDB','host')
        mysqlconf['user']   = self.cf.get('MYSQLDB','user')
        mysqlconf['passwd'] = self.cf.get('MYSQLDB','passwd')
        mysqlconf['port']   = self.cf.getint('MYSQLDB','port')
        
        mysqlconf['mincached']      = self.cf.getint('MYSQLDB','mincached')
        mysqlconf['maxcached']      = self.cf.getint('MYSQLDB','maxcached')
        mysqlconf['maxshared']      = self.cf.getint('MYSQLDB','maxshared')
        mysqlconf['maxconnections'] = self.cf.getint('MYSQLDB','maxconnections')
        mysqlconf['maxusage']       = self.cf.getint('MYSQLDB','maxusage')
        
        return mysqlconf

    def getStateConf(self):
        sttefile = {}
        sttefile['year']  = self.cf.getint('STATE','year')
        sttefile['month'] = self.cf.getint('STATE','month')
        sttefile['day']   = self.cf.getint('STATE','day')
        sttefile['hour']  = self.cf.getint('STATE','hour')
        return sttefile

    #获取NTP配置
    def getNTP(self):
        ntp = {}
        ntp['ip']  = self.cf.get('NTP','ip')
        return ntp

    def setStateConf(self,year,month,day,hour):
        self.cf.set('STATE', 'year', year)
        self.cf.set('STATE', 'month', month)
        self.cf.set('STATE', 'day', day)
        self.cf.set('STATE', 'hour', hour)
        fh = open('uploadsys.conf', 'w')
        self.cf.write(fh)
        fh.close()


class PlateIni:
    def __init__(self,confpath = 'uploadsys.conf'):
        self.path = ''
        self.confpath = confpath
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(self.confpath)

    def str2time(self,timestr):
        t = time.strptime(timestr,'%Y-%m-%d %H:%M:%S')
        return datetime.datetime(*t[:6])
        
    def getPlateInfo(self,inipath):
        self.cf.read(inipath)
        plateinfo = {}
        plateinfo['deviceid']       = self.cf.get('PLATEINFO','DeviceID')
        plateinfo['roadname']       = self.cf.get('PLATEINFO','RoadName')
        plateinfo['roadid']         = self.cf.get('PLATEINFO','RoadID')
        plateinfo['channelname']    = self.cf.get('PLATEINFO','ChannelName')
        plateinfo['channelid']      = self.cf.get('PLATEINFO','ChannelID')
        plateinfo['passdatetime']   = self.str2time(self.cf.get('PLATEINFO','PassDateTime')[:19])
        plateinfo['datetime']       = self.str2time(self.cf.get('PLATEINFO','DateTime')[:19])
        plateinfo['strtime']       = self.cf.get('PLATEINFO','PassDateTime')[:19]
        plateinfo['platecode']      = self.cf.get('PLATEINFO','PlateCode')
        plateinfo['platecolor']     = self.cf.get('PLATEINFO','PlateColor')
        plateinfo['platetype']      = self.cf.get('PLATEINFO','PlateType')
        plateinfo['vehiclelen']     = self.cf.get('PLATEINFO','VehicleLen')
        plateinfo['vehiclecolor']   = self.cf.get('PLATEINFO','VehicleColor')
        plateinfo['vehiclecoltype'] = self.cf.get('PLATEINFO','VehicleColType')
        plateinfo['speed']          = self.cf.getint('PLATEINFO','Speed')
        plateinfo['carspeed']       = self.cf.getint('PLATEINFO','CarSpeed')
        plateinfo['limitspeed']     = self.cf.getint('PLATEINFO','LimitSpeed')
        plateinfo['speedd']         = self.cf.getint('PLATEINFO','SpeedD')
        plateinfo['speedx']         = self.cf.getint('PLATEINFO','SpeedX')
        plateinfo['cameraip']       = self.cf.get('PLATEINFO','CameraIP')
        plateinfo['directionid']    = self.cf.get('PLATEINFO','DirectionId')
        plateinfo['channeltype']    = self.cf.get('PLATEINFO','ChannelType')
        return plateinfo


if __name__ == "__main__":
    PATH = 'F:/卡口/imgs/ImageFile/平潭乌塘卡口/20140304/11/1(出城)/20140113164737680_蓝牌粤B9041J.ini'
    #PATH2 = r'F:\\卡口\\imgs\\ImageFile\\测试卡口\1(出城)\20140113164737680_蓝牌粤B9041J.ini'
    PATH3 = 'F:\卡口\imgs\ImageFile\平潭乌塘卡口\20140304\11\test\20140113164940250_蓝牌粤LF2473.ini'

    import json
    imgIni = PlateIni()
    data = imgIni.getPlateInfo(PATH)
    print data
    s = json.dumps(data.decode('gbk'))
    print s
    a = json.loads(s)
    print a
    #s = str(imgIni.getPlateInfo(PATH))
    #print (d1,1)
    #time.sleep(30)



