import time
import ntplib
import win32api

class NtpClient:
    def __init__(self,ip):
        self.ip = ip
        self.c = ntplib.NTPClient()

    def __del__(self):
        del self.c
        
    def setTime(self):
        response = self.c.request(self.ip)
        ts = response.tx_time
        tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.localtime(ts-28800)
        win32api.SetSystemTime(tm_year, tm_mon, tm_wday, tm_mday, tm_hour, tm_min, tm_sec, 0) 
        return ts
    
if __name__ == "__main__":
    s = 'cn.pool.ntp.org'
    s2 = '210.72.145.44'
    s3 = '127.0.0.1'
    ntp = NtpClient(s3)
    ts = ntp.setTime()
    print (time.strftime('%Y-%m-%d %X', time.localtime(ts)),)
    del ntp

