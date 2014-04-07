#-*- encoding: gb2312 -*-
import ConfigParser
import string, os, sys
import datetime
import time


class ImgIni:
    def __init__(self,confpath = 'dataclient.conf'):
        self.path = ''
        self.confpath = confpath
        #print self.confpath
        #self.cf = ConfigParser.ConfigParser()
        
    def str2time(self,timestr):
        t = time.strptime(timestr,'%Y-%m-%d %H:%M:%S')
        return datetime.datetime(*t[:6])

    def getPlateInfo(self,path):
        self.path = path
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(self.path)
        plateinfo = {}
        plateinfo['deviceid']       = self.cf.get('PLATEINFO','DeviceID').decode('gbk').encode('utf8')
        plateinfo['roadname']       = self.cf.get('PLATEINFO','RoadName').decode('gbk').encode('utf8')
        plateinfo['roadid']         = self.cf.get('PLATEINFO','RoadID').decode('gbk').encode('utf8')
        plateinfo['channelname']    = self.cf.get('PLATEINFO','ChannelName').decode('gbk').encode('utf8')
        plateinfo['channelid']      = self.cf.get('PLATEINFO','ChannelID').decode('gbk').encode('utf8')
        plateinfo['passdatetime']   = self.str2time(self.cf.get('PLATEINFO','PassDateTime'))
        plateinfo['datetime']       = self.str2time(self.cf.get('PLATEINFO','DateTime'))
        plateinfo['platecode']      = self.cf.get('PLATEINFO','PlateCode').decode('gbk').encode('utf8')
        plateinfo['platecolor']     = self.cf.get('PLATEINFO','PlateColor').decode('gbk').encode('utf8')
        plateinfo['platetype']      = self.cf.get('PLATEINFO','PlateType').decode('gbk').encode('utf8')
        plateinfo['vehiclelen']     = self.cf.get('PLATEINFO','VehicleLen').decode('gbk').encode('utf8')
        plateinfo['vehiclecolor']   = self.cf.get('PLATEINFO','VehicleColor').decode('gbk').encode('utf8')
        plateinfo['vehiclecoltype'] = self.cf.get('PLATEINFO','VehicleColType').decode('gbk').encode('utf8')
        plateinfo['speed']          = self.cf.getint('PLATEINFO','Speed')
        plateinfo['carspeed']       = self.cf.getint('PLATEINFO','CarSpeed')
        plateinfo['limitspeed']     = self.cf.getint('PLATEINFO','LimitSpeed')
        plateinfo['speedd']         = self.cf.getint('PLATEINFO','SpeedD')
        plateinfo['speedx']         = self.cf.getint('PLATEINFO','SpeedX')
        plateinfo['cameraip']       = self.cf.get('PLATEINFO','CameraIP').decode('gbk').encode('utf8')
        plateinfo['directionid']    = self.cf.get('PLATEINFO','DirectionId').decode('gbk').encode('utf8')
        plateinfo['channeltype']    = self.cf.get('PLATEINFO','ChannelType').decode('gbk').encode('utf8')
        return plateinfo
    
    def getImgFileConf(self):
        cf = ConfigParser.ConfigParser()
        #print self.imgfilepath
        cf.read('dataclient.conf')
        imgfile = {}
        imgfile['imgpath'] = cf.get('IMGFILE','imgpath')
        imgfile['ip'] = cf.get('IMGFILE','ip')
        return imgfile

    def getMysqldbConf(self):
        cf = ConfigParser.ConfigParser()
        cf.read('dataclient.conf')
        mysqlconf = {}
        mysqlconf['host']    = cf.get('MYSQLDB','host')
        mysqlconf['user']    = cf.get('MYSQLDB','user')
        mysqlconf['passwd']  = cf.get('MYSQLDB','passwd')
        mysqlconf['port']    = cf.getint('MYSQLDB','port')
        mysqlconf['db']      = cf.get('MYSQLDB','db')
        mysqlconf['charset'] = cf.get('MYSQLDB','charset')
        return mysqlconf

class FtpIni:
    def __init__(self,filename = 'ftpclient.conf'):
        #self.confpath = confpath
        self.cf = ConfigParser.ConfigParser()
        self.filename = 'ftpclient.conf'
        self.cf.read(self.filename)

    def getFtpConf(self):
        ftpset = {}
        ftpset['imgpath'] = self.cf.get('FTPSET','imgpath')
        ftpset['host']    = self.cf.get('FTPSET','host')
        ftpset['user']    = self.cf.get('FTPSET','user')
        ftpset['passwd']  = self.cf.get('FTPSET','passwd')
        ftpset['port']    = self.cf.get('FTPSET','port')
        ftpset['bufsize'] = self.cf.get('FTPSET','bufsize')
        return ftpset

    def getMysqlConf(self):
        mysqlconf = {}
        mysqlconf['host']    = self.cf.get('MYSQLSET','host')
        mysqlconf['user']    = self.cf.get('MYSQLSET','user')
        mysqlconf['passwd']  = self.cf.get('MYSQLSET','passwd')
        mysqlconf['port']    = self.cf.getint('MYSQLSET','port')
        #mysqlconf['db']      = cf.get('MYSQLSET','db')
        #mysqlconf['charset'] = cf.get('MYSQLSET','charset')
        return mysqlconf

    def getDiskConf(self):
        diskconf = {}
        diskconf['disklist']   = self.cf.get('STORAGE','disklist')
        diskconf['activedisk'] = self.cf.get('STORAGE','activedisk')
        return diskconf

    def setDiskConf(self,disk):
        self.cf.set('STORAGE', 'activedisk', disk)
        fh = open('ftpclient.conf', 'w')
        self.cf.write(fh)
        fh.close()

class DataCenterIni:
    def __init__(self,confpath = 'datacenter.conf'):
        self.confpath = confpath

    def getSyst(self):
        cf = ConfigParser.ConfigParser()
        cf.read('datacenter.conf')
        syst = {}
        syst['disk']       = cf.get('SYST','disk')
        syst['activedisk'] = cf.get('SYST','activedisk')
        return syst
    
    def getOrcConf(self):
        cf = ConfigParser.ConfigParser()
        cf.read('datacenter.conf')
        orcconf = {}
        orcconf['host']   = cf.get('ORCSET','host')
        orcconf['user']   = cf.get('ORCSET','user')
        orcconf['passwd'] = cf.get('ORCSET','passwd')
        orcconf['port']   = cf.get('ORCSET','port')
        orcconf['sid']    = cf.get('ORCSET','sid')
        return orcconf

    def getMysqlConf(self):
        cf = ConfigParser.ConfigParser()
        cf.read('datacenter.conf')
        section = 'MYSQLSET'
        #print 'section',section
        mysqlconf = {}
        mysqlconf['host']    = cf.get(section,'host')
        mysqlconf['user']    = cf.get(section,'user')
        mysqlconf['passwd']  = cf.get(section,'passwd')
        mysqlconf['port']    = cf.getint(section,'port')
        mysqlconf['db']      = cf.get(section,'db')
        mysqlconf['charset'] = cf.get(section,'charset')
        return mysqlconf
    
##def getTime():
##    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

if __name__ == "__main__":
    #PATH = 'F:/卡口/imgs/ImageFile/平潭乌塘卡口/20140304/11/1(出城)/20140113164737680_蓝牌粤B9041J.ini'
    PATH2 = 'F:\\卡口\\imgs\\ImageFile\\平潭乌塘卡口\\20140304\\11\\1(出城)\\20140113164737680_蓝牌粤B9041J.ini'
    #PATH3 = 'F:\卡口\imgs\ImageFile\平潭乌塘卡口\20140304\11\test\20140113164940250_蓝牌粤LF2473.ini'
##    print "r'"+PATH2+"'"
    try:
        imgIni = ImgIni()
        #ftpini.setDiskConf()
        plateinfo = imgIni.getPlateInfo(PATH2)
        direction = {'0':u'进城','1':u'出城','2':u'由东往西','3':u'由南往北','4':u'由西往东','5':u'由北往南'}
        s = direction.get(plateinfo['directionid'],u'其他')
        print s
        carstr = '%s %s  %s | %s %s'%(getTime(),plateinfo['platecode'].decode("utf-8").encode("gbk"),plateinfo['platecolor'].decode("utf-8").encode("gbk"),direction.get(plateinfo['directionid'],u'其他').encode("gbk"),plateinfo['channelid'].decode("utf-8").encode("gbk"))
        #carstr = '%s  %s | %s %s'%(plateinfo['platecode'],plateinfo['platecolor'],s.encode('utf-8'),plateinfo['channelid'])
        print carstr
        #i = s['host'].split(',')
        #print s
        #disk = s['disk'].split(',')
        #print disk
        #del i
    except ConfigParser.NoOptionError,e:
        print e
        time.sleep(10)
    #print s['path']

#print cf.sections()
#s = cf.get('')
