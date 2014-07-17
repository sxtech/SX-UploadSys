# -*- coding: cp936 -*-
import os
import sys
import glob
import time
import datetime
import MySQLdb
import gl

def getTime():
    return datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

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

class UMysql:
    def __init__(self):
        #print '12345'
        self.conn  = gl.mysqlpool.connection()
        self.cur   = self.conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        self.table = 'indexcenter'
        
    def __del__(self):
        try:
            self.conn.close()
            self.cur.close()
        except Exception,e:
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
    
    def getDiskByFlag(self):
        try:
            self.cur.execute("select * from disk where flag=1 and disabled=0")
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getDisk(self):
        try:
            self.cur.execute("select * from disk order by id desc limit 0,1")
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getDiskByIP(self,ip):
        try:
            self.cur.execute("select * from disk where d_ip='%s'"%ip)
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getDiskBySel(self,ip,disk):
        self.cur.execute("select * from disk where d_ip='%s' and disk='%s' and disabled=0"%(ip,disk))
        s = self.cur.fetchone()
        self.conn.commit()
        return s

    def addDisk(self,ip,disk):
        self.cur.execute("insert into disk(d_ip,disk) values(%s,%s)",(ip,disk))
        self.conn.commit()

        
    def setDisk(self,ip,disk):
        try:
            self.cur.execute("insert into disk(d_ip,disk) values(%s,%s)",(ip,disk))
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()

    def setDisk2(self,ip,disk,size,freespace):
        self.cur.execute("insert into disk(d_ip,disk,size,freespace) values(%s,%s,%s,%s)",(ip,disk,size,freespace))
        self.conn.commit()

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
            endtime = self.initime + datetime.timedelta(minutes = 60)
            self.cur.execute("(select captime from indexcenter where captime>=%s and captime<=%s and iniflag=0 ORDER BY captime limit 0,1)  union all (select captime from indexcenter where iniflag=1 and captime>=%s and captime<=%s ORDER BY captime desc limit 0,1) ORDER BY captime limit 0,1",(self.initime,endtime,self.initime,endtime))
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
            endtime = self.imgtime + datetime.timedelta(minutes = 60)
            self.cur.execute("(select captime from indexcenter where captime>=%s and captime<=%s and imgflag=0 ORDER BY captime limit 0,1) union all (select captime from indexcenter where imgflag=1 and captime>=%s and captime<=%s ORDER BY captime desc limit 0,1) ORDER BY captime limit 0,1",(self.imgtime,endtime,self.imgtime,endtime))
            new_imgtime = self.cur.fetchone()
            self.conn.commit()
            if new_imgtime==None:
                new_imgtime={}
                new_imgtime['captime']=self.imgtime
            self.cur.execute("update timeflag set imgtime=%s where id=1",new_imgtime['captime'])
            self.conn.commit()
            self.imgtime=new_imgtime['captime'] - datetime.timedelta(minutes = 5)
        except MySQLdb.Error,e:
            raise
        
    def getLastDatafolder(self):
        try:
            self.cur.execute('select datefolder from indexcenter where pcip=%s ORDER BY datefolder DESC limit 0,1'%self.ip)
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def addIndex(self,values):
        try:
            self.cur.executemany('insert into indexcenter(datefolder,hour,pcip,captime,imgfile,imgpath,deviceid,roadname,roadid,channelname,channelid,passdatetime,datetime,platecode,platecolor,platetype,vehiclelen,vehiclecolor,vehiclecoltype,speed,carspeed,limitspeed,speedd,speedx,overspeed,cameraip,directionid,channeltype) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', values)
        except MySQLdb.Error,e:
            raise
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
            self.cur.execute("select i.id,i.pcip,i.imgfile,i.imgpath,i.platecode,i.platecolor,i.roadname,i.directionid,i.channelid,i.pcip,d.d_ip,d.disk from indexcenter as i LEFT JOIN disk as d on i.disk_id = d.id where (i.captime>='%s' or (i.captime>='%s' and i.captime<='%s')) and i.imgflag = 0 and i.pcip in('%s') order by i.passdatetime desc limit 0,%s"%(datetime.datetime.now()-datetime.timedelta(minutes=10),self.imgtime,self.imgtime+datetime.timedelta(minutes=30),strip,limit))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s
        
    def getIndexByTime(self,date,hour):
        try:
            self.cur.execute("select * from indexcenter where datefolder='%s' and hour=%s and pcip=%s"%(date,hour,self.ip))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getImgfileByTime(self,date,hour,ip):
        try:
            self.cur.execute("select imgfile from %s where datefolder='%s' and hour=%s and pcip=%s"%(self.table,date,hour,ip))
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
        
    #main
    def getPlateInfo(self,limit=10):
        try:
            if self.imgtime == None:
                self.getLastFlagTime()
            self.cur.execute("select i.*,d.d_ip,d.disk from indexcenter as i left join disk as d on i.disk_id=d.id where (i.captime>=%s or (i.captime>=%s and i.captime<=%s)) and i.iniflag=0 ORDER BY i.passdatetime DESC limit 0,%s",(datetime.datetime.now()-datetime.timedelta(minutes=10),self.initime,self.initime+datetime.timedelta(minutes=30),limit))
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def test(self):
        try:
            self.cur.execute("select * from indexcenter where id = 1")
            s = self.cur.fetchall()
        except MySQLdb.Error,e:
            raise
        else:
            self.conn.commit()
            return s

    def getVersion(self):
        try:
            self.cur.execute("select version()")
            s = self.cur.fetchone()
        except MySQLdb.Error,e:
            raise
        else:
            return s
        
    def endOfCur(self):
        self.conn.commit()
        
    def sqlCommit(self):
        self.conn.commit()
        
    def sqlRollback(self):
        self.conn.rollback()
            
if __name__ == "__main__":
    from DBUtils.PooledDB import PooledDB
    try:
        mysqlPool('localhost','root','',3306)
        imgMysql = ImgMysql()
        #imgMysql.setupMysql()

        #s = imgMysql.getImgfileByTime('2014-01-16',15,2130706433)
        #print s
        #imgMysql.setNewFlagTime()
        #s = imgMysql.getImgInfoByIPList(10,['127.0.0.1'])
        #print imgMysql.getDisk()['id']
        #imgMysql.setDisk('192.168.1.12','E')
        #time.sleep(5)
        
    except MySQLdb.Error,e:
        print e
    else:
        pass
        #del imgMysql

