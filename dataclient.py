# -*- coding: cp936 -*-
import time,datetime,os,glob,sys
import MySQLdb
import logging
import logging.handlers
import cPickle
import ConfigParser
from mysqldb import ImgMysql
from inicof import ImgIni
from singleinstance import singleinstance


def getTime():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            
def initLogging(logFilename):
    """Init for logging"""
    path = os.path.split(logFilename)
    if os.path.isdir(path[0]):
        pass
    else:
        os.makedirs(path[0])
    logging.basicConfig(
                    level    = logging.DEBUG,
                    format   = '%(asctime)s %(filename)s[line:%(lineno)d] [%(levelname)s] %(message)s',
                    datefmt  = '%Y-%m-%d %H:%M:%S',
                    filename = logFilename,
                    filemode = 'a');

def version():
    return 'SX-dataclient V0.4.8'

class DataClient:
    def __init__(self,trigger):
        self.trigger = trigger
        self.style_red = 'size=4 face=arial color=red'
        self.style_blue = 'size=4 face=arial color=blue'
        self.style_green = 'size=4 face=arial color=green'
        
        #self.trigger.emit("<font %s>%s</font>"%(self.style_green,'Welcome to '+version()))
        initLogging(r'log\dataclient.log')
        self.file_list = []
        self.ACTIVE_FOLDER = ()
        self.DIC_FILE = {}
        self.ACTIVE_TIME = datetime.datetime(2000,01,01,00,00,00)
        self.direction = {'0':'����','1':'����','2':'�ɶ�����','3':'��������','4':'��������','5':'�ɱ�����'}

        self.imgIni = ImgIni()
        mysqlconf = self.imgIni.getMysqldbConf()
        imgconf = self.imgIni.getImgFileConf()
        self.imgMysql = ImgMysql(mysqlconf['host'],mysqlconf['user'],mysqlconf['passwd'],imgconf['ip'])
        self.path = imgconf['imgpath']
        self.ip = imgconf['ip']
        self.KAKOU = os.listdir(imgconf['imgpath'])
        self.errorfile = []
        self.filename = ''
        self.disk_id = 1

    def __del__(self):
        del self.imgMysql
        logging.info('dataclient quit')
        #self.trigger.emit("<font %s>%s</font>"%(self.style_green,getTime(),'System quit')) 

    def setup(self):
        try:
            self.trigger.emit("<font %s>%s</font>"%(self.style_green,getTime()+'Start to connect mysql server '+self.imgMysql.host))
            self.imgMysql.login()
            self.trigger.emit("<font %s>%s</font>"%(self.style_green,getTime()+'Connect mysql success! '+self.imgMysql.host))
        except Exception,e:
            now = getTime()
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,now+str(e)))
            logging.exception(e)
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,now+'Reconn after 15 seconds'))
            time.sleep(15)
            self.setup()
        else:
            pass
            logging.info('Connect mysql success!')
            
    def loginsql(self):
        self.imgMysql.login()
            
    def setip(self):
        self.imgMysql.setip()
            
    def set_kakou(self):
        imgconf = self.imgIni.getImgFileConf()
        self.KAKOU = os.listdir(imgconf['imgpath'])
        
    def setState(self):
        f =file('state.data','w')
        cPickle.dump(self.ACTIVE_FOLDER,f)
        cPickle.dump(self.ACTIVE_TIME,f)
        cPickle.dump(self.DIC_FILE,f)
        f.close()

    def getDiskID(self):
        self.disk_id = self.imgMysql.getDisk()['id']
        
    def getState(self):
        f =file('state.data','r')
        try:
            self.ACTIVE_FOLDER = cPickle.load(f)
            self.ACTIVE_TIME   = cPickle.load(f)
            self.DIC_FILE      = cPickle.load(f)
        except EOFError:
            f.close()

    def builtErrorFile(self):
        if os.path.isfile('errorfile.data') == False:
            self.setErrorFile()
            self.trigger.emit("<font %s>%s</font>"%(self.style_green,getTime()+'built errorfile'))
            
    def setErrorFile(self):
        f =file('errorfile.data','w')
        cPickle.dump(self.errorfile,f)
        f.close()

    def getErrorFile(self):
        f =file('errorfile.data','r')
        try:
            self.errorfile = cPickle.load(f)
        except EOFError:
            f.close()
            
    def get_time_active_folder(self):
        d_time = datetime.datetime.now()
        return (d_time.strftime('%Y%m%d'),d_time.strftime('%H'),d_time)
        

    def get_last_active_file(self):
        df = self.imgMysql.getLastDatafolder()
        ini_set = set()

        if df != None:
            for row in self.imgMysql.getIndexByTime(df['datefolder']):
                ini_set.add(row['inifile'])
            date = df['datefolder'].strftime('%Y%m%d')
            hour = df['datefolder'].strftime('%H')
            self.ACTIVE_TIME = df['datefolder']
        else:
            i = datetime.datetime.now()
            date = i.strftime('%Y%m%d')
            hour = i.strftime('%H')
            self.ACTIVE_TIME = datetime.datetime(i.year,i.month,i.day,i.hour,00,00)
            
        self.DIC_FILE[(date,hour)] = ini_set
        self.ACTIVE_FOLDER = (date,hour)
        self.setState()

    def get_new_ini(self,date,hour):
        new_ini = set()
        path_len = len(self.path)
        try:
            for i in self.KAKOU:
                f = glob.glob(self.path+i+os.sep+date+os.sep+hour+'\*\*.ini')
                for j in f:
                    new_ini.add(j[path_len:].decode("gbk"))
        except Exception,e:
            #self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
            raise
        else:
            pass
        finally:
            return new_ini
                
    def add_index(self,date,hour,d_time):
        new_ini = self.get_new_ini(date,hour)
        old_ini = set()
        try:
            old_ini = self.DIC_FILE[(date,hour)]
        except KeyError,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+'KeyError'+str(e)))
            self.DIC_FILE[(date,hour)] = old_ini
            self.setState()
            for i in self.imgMysql.getInifileByTime(d_time):
                old_ini.add(i['inifile'])
                
        ca_ini = new_ini - old_ini

        f_name = list(ca_ini)
        f_name.sort()

        values = []
        time = datetime.datetime.now()

        plateinfo = {}
        if len(f_name) != 0:
            for i in range(len(f_name)):
                try:
                    #self.filename = f_name[i]
                    plateinfo = self.imgIni.getPlateInfo(self.path.decode("gbk")+f_name[i])
                    if plateinfo['carspeed'] > plateinfo['limitspeed']:
                        overspeed = 100.0*(plateinfo['carspeed']/plateinfo['limitspeed']-1)
                    else:
                        overspeed = 0.0
                    imgpath = date+'\\'+hour+'\\'+plateinfo['cameraip']+'\\'+plateinfo['channelid']+'\\'+os.path.basename(f_name[i])[:17]+'.jpg'
                    values.append((d_time,self.ip.encode("utf-8"),time,f_name[i].encode("utf-8"),self.disk_id,imgpath.encode("utf-8"),plateinfo['deviceid'],plateinfo['roadname'],plateinfo['roadid'],plateinfo['channelname'],plateinfo['channelid'],plateinfo['passdatetime'],plateinfo['datetime'],plateinfo['platecode'],plateinfo['platecolor'],plateinfo['platetype'],plateinfo['vehiclelen'],plateinfo['vehiclecolor'],plateinfo['vehiclecoltype'],plateinfo['speed'],plateinfo['carspeed'],plateinfo['limitspeed'],plateinfo['speedd'],plateinfo['speedx'],overspeed,plateinfo['cameraip'],plateinfo['directionid'],plateinfo['channeltype']))
                except ConfigParser.NoOptionError,e:
                    self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
                    logging.exception(e)
                    #logging.error('filename: '+f_name[i])
                    self.errorfile.append((f_name[i],date,hour,d_time))
                    self.setErrorFile()
            if self.imgMysql.addIndex(values) == True:
                self.DIC_FILE[(date,hour)] = new_ini
                carstr = '[%s]  %s  %s |'%(plateinfo['passdatetime'],plateinfo['platecode'],plateinfo['platecolor']),'%s |'%self.direction.get(plateinfo['directionid'],'����'),'%s����'%plateinfo['channelid']
                self.trigger.emit("<font %s>%s</font>"%(self.style_blue,carstr))
                self.setState()
            else:
                pass

    def setActiveTime(self):
        self.imgMysql.setActiveTime(datetime.datetime.now())

    def appendIndex(self):
        values = []
        time = datetime.datetime.now()
        for filename in self.errorfile:
            try:
                plateinfo = self.imgIni.getPlateInfo(self.path.decode("gbk")+filename[0])
                if plateinfo['carspeed'] > plateinfo['limitspeed']:
                    overspeed = 100.0*(plateinfo['carspeed']/plateinfo['limitspeed']-1)
                else:
                    overspeed = 0.0
                imgpath = filename[1]+'\\'+filename[2]+'\\'+plateinfo['cameraip']+'\\'+plateinfo['channelid']+'\\'+os.path.basename(filename[0])[:17]+'.jpg'
                values.append((filename[3],self.ip.encode("utf-8"),time,filename[0].encode("utf-8"),self.disk_id,imgpath.encode("utf-8"),plateinfo['deviceid'],plateinfo['roadname'],plateinfo['roadid'],plateinfo['channelname'],plateinfo['channelid'],plateinfo['passdatetime'],plateinfo['datetime'],plateinfo['platecode'],plateinfo['platecolor'],plateinfo['platetype'],plateinfo['vehiclelen'],plateinfo['vehiclecolor'],plateinfo['vehiclecoltype'],plateinfo['speed'],plateinfo['carspeed'],plateinfo['limitspeed'],plateinfo['speedd'],plateinfo['speedx'],overspeed,plateinfo['cameraip'],plateinfo['directionid'],plateinfo['channeltype']))
                
            except ConfigParser.NoOptionError,e:
                #print getTime(),e
                self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
                self.trigger.emit("<font %s>%s</font>"%(self.style_red,'failfile: '+filename[0]))
            except Exception,e:
                #print getTime(),e
                self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
                self.trigger.emit("<font %s>%s</font>"%(self.style_red,'failfile: '+filename[0]))
                
        if self.imgMysql.addIndex(values) == True:
            self.trigger.emit("<font %s>%s</font>"%(self.style_green,getTime()+'Update missed %d files'%len(self.errorfile)))
        self.errorfile = []
        self.setErrorFile()

    def cmp_active_folder(self):
        try:
            new_time = self.get_time_active_folder()
            self.add_index(self.ACTIVE_FOLDER[0],self.ACTIVE_FOLDER[1],self.ACTIVE_TIME)
            trailing_time = self.ACTIVE_TIME+datetime.timedelta(minutes = 59)
            right_time    = self.ACTIVE_TIME+datetime.timedelta(minutes = 60)
            rising_time   = self.ACTIVE_TIME+datetime.timedelta(minutes = 61)
            if new_time[2] > trailing_time:
                self.add_index(new_time[0],new_time[1],datetime.datetime(new_time[2].year,new_time[2].month,new_time[2].day,new_time[2].hour,00,00))
                if new_time[2] > rising_time:
                    del self.DIC_FILE[(self.ACTIVE_FOLDER[0],self.ACTIVE_FOLDER[1])]
                    self.ACTIVE_FOLDER = (right_time.strftime('%Y%m%d'),right_time.strftime('%H'))
                    self.ACTIVE_TIME = right_time
                    self.setState()

        except MySQLdb.Error,e:
            #self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
            #logging.exception(e)
            raise
        except Exception,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
            logging.exception(e)
            time.sleep(1)

    def setFlagTime(self):
        try:
            self.imgMysql.setFlagTime()
        except Exception,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
