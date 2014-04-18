# -*- coding: cp936 -*-
import os
import sys
import glob
import time
import datetime
import MySQLdb

def getTime():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

class ImgMysql:
    def __init__(self,host = '',user = '', passwd = '',ip='127.0.0.1'):
        self.host    = host
        self.user    = user
        self.passwd  = passwd
        self.port    = 3306
        self.db      = 'img_center'
        self.charset = 'utf8'
        self.ip = ip
        self.initime = None
        self.imgtime = None
        self.cur = None
        self.conn = None
        
    def __del__(self):
        if self.cur != None:
            self.cur.close()
        if self.conn != None:
            self.conn.close()

    def login(self):
        try:
            self.conn = MySQLdb.connect(host=self.host,user=self.user,passwd=self.passwd,
                                        port=self.port,charset=self.charset,db=self.db)
            self.cur = self.conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        except MySQLdb.Error,e:
            raise
        except Exception,e:
            raise

    def setupMysql(self):
        now = getTime()
        try:
            self.login()
        except Exception,e:
            #print now,e
            #print now,'Reconn after 15 seconds'
            time.sleep(15)
            self.setupMysql()
        else:
            pass

    def getActiveTime(self,ip):
        try:
            self.cur.execute("select * from iplist where ip=%s",ip)
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s
        
    def setActiveTime(self,t):
        try:
            self.cur.execute("update iplist set activetime=%s where ip=%s",(t,self.ip))
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
    
    def getDisk(self):
        try:
            self.cur.execute("select * from disk order by id desc limit 0,1")
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s
        
    def setDisk(self,ip,disk):
        try:
            self.cur.execute("insert into disk(d_ip,disk) values(%s,%s)",(ip,disk))
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s
        
    def getLastFlagTime(self):
        try:
            self.cur.execute("select initime,imgtime from timeflag where id=1")
            s = self.cur.fetchone()
            self.initime=s['initime']
            self.imgtime=s['imgtime']
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def setNewIniTime(self):
        try:
            if self.imgtime == None:
                self.getLastFlagTime()
            self.cur.execute("(select captime from indexcenter where iniflag=0 and captime>=%s ORDER BY captime limit 0,1)  union all (select captime from indexcenter where iniflag=1 and captime>=%s ORDER BY captime desc limit 0,1) ORDER BY captime limit 0,1",(self.initime,self.initime))
            new_initime = self.cur.fetchone()
            self.conn.commit()
            if new_initime==None:
                new_initime={}
                new_initime['captime']=self.initime
            self.cur.execute("update timeflag set initime=%s where id=1",new_initime['captime'])
            self.conn.commit()
            self.initime=new_initime['captime'] - datetime.timedelta(minutes = 1)
        except MySQLdb.Error,e:
            raise

    def setNewImgTime(self):
        try:
            if self.imgtime == None:
                self.getLastFlagTime()
            self.cur.execute("(select captime from indexcenter where imgflag=0 and captime>=%s ORDER BY captime limit 0,1) union all (select captime from indexcenter where imgflag=1 and captime>=%s ORDER BY captime desc limit 0,1) ORDER BY captime limit 0,1",(self.imgtime,self.imgtime))
            new_imgtime = self.cur.fetchone()
            self.conn.commit()
            if new_imgtime==None:
                new_imgtime={}
                new_imgtime['captime']=self.imgtime
            self.cur.execute("update timeflag set imgtime=%s where id=1",new_imgtime['captime'])
            self.conn.commit()
            self.imgtime=new_imgtime['captime'] - datetime.timedelta(minutes = 1)
        except MySQLdb.Error,e:
            raise
        
    def getLastDatafolder(self):
        try:
            self.cur.execute('select datefolder from indexcenter where pcip=%s ORDER BY datefolder DESC limit 0,1',self.ip)
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def addIndex(self,values):
        try:
            self.cur.executemany('insert into indexcenter(datefolder,pcip,captime,inifile,disk_id,imgpath,deviceid,roadname,roadid,channelname,channelid,passdatetime,datetime,platecode,platecolor,platetype,vehiclelen,vehiclecolor,vehiclecoltype,speed,carspeed,limitspeed,speedd,speedx,overspeed,cameraip,directionid,channeltype) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', values)
        except MySQLdb.Error,e:
            self.conn.rollback()
            return False
        else:
            self.conn.commit()
            return True
        
    def setip(self,fid=0):
        try:
            self.cur.execute("select * from iplist where ip=%s",self.ip)
            self.conn.commit()
            if self.cur.fetchone() == None:
                self.cur.execute("insert into iplist(fid,ip) values(%s,%s)",(fid,self.ip))
                self.conn.commit()
        except MySQLdb.Error,e:
            self.conn.rollback()
        else:
            return True

    def getip(self,fid=0):
        try:
            self.cur.execute("select ip from iplist where fid=%s",fid)
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getIPList(self,fid=0):
        try:
            self.cur.execute("select * from iplist where fid=%s",fid)
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getNewIP(self,ip=[]):
        try:
            strip = "','".join(ip)
            self.cur.execute("select ip from iplist where ip not in('%s')"%strip)
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s
        
    #main
    def getImgInfoByIPList(self,limit=10,ip=[]):
        try:
            if self.imgtime == None:
                self.getLastFlagTime()
            strip = "','".join(ip)
            self.cur.execute("select i.id,i.pcip,i.inifile,i.imgpath,i.platecode,i.platecolor,i.roadname,i.directionid,i.channelid,i.pcip,d.d_ip,d.disk from indexcenter as i LEFT JOIN disk as d on i.disk_id = d.id where i.imgflag = 0 and i.pcip in('%s') and i.captime>='%s' order by i.passdatetime desc limit 0,%s"%(strip,self.imgtime,limit))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s
        
    def getIndexByTime(self,time):
        try:
            self.cur.execute('select * from indexcenter where datefolder=%s and pcip=%s',(time,self.ip))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getInifileByTime(self,time):
        try:
            self.cur.execute('select inifile from indexcenter where datefolder=%s and pcip=%s',(time,self.ip))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def flagImgIndex(self,index_id,imgflag=1):
        s=False
        try:
            self.cur.execute('update indexcenter set imgflag=%s where id=%s',(imgflag,index_id))
        except MySQLdb.Error,e:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()
            s=True
        finally:
            return s

    def flagManyImgIndex(self,index_id):
        s=False
        try:
            self.cur.execute('update indexcenter set imgflag=1 where id=%s',index_id)
        except MySQLdb.Error,e:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()
            s=True
        finally:
            return s
        
    def flagManyIniIndex(self,index_id):
        try:
            self.cur.execute("update indexcenter set iniflag=1 where id=%s",index_id)
        except MySQLdb.Error,e:
            return False
            self.conn.rollback()
            raise
            
    def endOfCur(self):
        self.conn.commit()
        
    def sqlCommit(self):
        self.conn.commit()
        
    def sqlRollback(self):
        self.conn.rollback()

    #main
    def getPlateInfo(self,limit=10):
        try:
            if self.imgtime == None:
                self.getLastFlagTime()
            self.cur.execute("select i.*,d.d_ip,d.disk from indexcenter as i left join disk as d on i.disk_id=d.id where i.iniflag=0 and i.captime>=%s ORDER BY i.passdatetime DESC limit 0,%s",(self.initime,limit))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

            
if __name__ == "__main__":
    try:
        imgMysql = ImgMysql('localhost','root','','127.0.0.1')
        imgMysql.setupMysql()

        s = imgMysql.getIPList()
        print s

        time.sleep(5)

    except MySQLdb.Error,e:
        print e
    else:
        pass
        #del imgMysql

