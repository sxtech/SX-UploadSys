from dataclient import DataClient
from PyQt4 import QtGui, QtCore
import sys,time,datetime,os
import MySQLdb
import logging
import logging.handlers
from singleinstance import singleinstance
import gl

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
    return 'SX-UploadSys V0.1.4'

 
class MyThread(QtCore.QThread):
    trigger = QtCore.pyqtSignal(str)
 
    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent)
 
    def run(self):
        #mainloop(self.trigger)
        m = dcmain(self.trigger)
        m.mainloop()

class dcmain:
    def __init__(self,trigger):
        self.style_red = 'size=4 face=arial color=red'
        self.style_blue = 'size=4 face=arial color=blue'
        self.style_green = 'size=4 face=arial color=green'
        self.trigger = trigger
        initLogging(r'log\dataclient.log')
        self.dc = DataClient(trigger)
        self.count = 0
        self.loginflag = True
        self.logincount = 0
        self.setupflag = False

        self.trigger.emit("<font %s>%s</font>"%(self.style_green,'Welcome to '+version()))


    def __del__(self):
        del self.dc

    def loginSQL(self):
        now = getTime()
        try:
            self.trigger.emit("<font %s>%s</font>"%(self.style_green,now+'Start to connect mysql server '))
            self.dc.loginsql()
            self.trigger.emit("<font %s>%s</font>"%(self.style_green,now+'Connect mysql success! '))
        except MySQLdb.Error,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,now+str(e)))
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,now+'Reconn after 15 seconds'))
            logging.exception(e)
            self.loginflag = True
            self.logincount = 1
        except Exception,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,now+str(e)))
            logging.exception(e)
        else:
            self.loginflag = False
            self.logincount = 0
##        finally:
##            self.checkFlag()

    def comLoop(self):
        #print 'loop'
        try:   
            if len(self.dc.errorfile) > 0:
                self.dc.appendIndex()
            self.dc.cmp_active_folder()
            
            if self.count%40 == 0:
                self.dc.setActiveTime()
            if self.count >=120:
                self.count = 0
                self.dc.set_kakou()
                self.dc.getDiskID()
                self.trigger.emit("<font %s>%s</font>"%(self.style_green,getTime()+'Activing folder %s/%s'%(self.dc.ACTIVE_FOLDER[0],self.dc.ACTIVE_FOLDER[1])))
                #self.count = 0
        except MySQLdb.Error,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
            logging.exception(e)
            self.loginflag = True
            self.logincount = 1
        except Exception,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,now+str(e)))
            logging.exception(e)
        finally:
            self.count += 1
            time.sleep(0.25)
            #self.checkFlag()
        
    def setup(self):
        #print 'setup'
        try:
            self.dc.setip()
            self.dc.getDiskID()
            try:
                self.dc.getState()
            except IOError,e:
                print e
                if e[0]==2:
                    self.dc.get_last_active_file()
            self.dc.builtErrorFile()
            self.dc.getErrorFile()
        except MySQLdb.Error,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
            logging.exception(e)
            self.loginflag = True
            self.logincount = 1
            #self.checkFlag()
        except Exception,e:
            self.trigger.emit("<font %s>%s</font>"%(self.style_red,getTime()+str(e)))
            logging.exception(e)
            #self.checkFlag()
        else:
            self.setupflag = True
        #finally:
            #self.comLoop()

    def mainloop(self):                    
        while True:
            #print 'count ',self.count
            if gl.qtflag == False:
                gl.dcflag = False
                break
            
            if self.loginflag == True:
                if self.logincount==0:
                    self.loginSQL()
                elif self.logincount<=15:
                    self.logincount += 1
                    time.sleep(1)
                    #self.checkFlag()
                else:
                    self.logincount = 0
                    #self.checkFlag()
            else:
                #print 'self.setupflag',self.setupflag
                if self.setupflag:
                    self.comLoop()
                else:
                    self.setup()
    
class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):  
        super(MainWindow, self).__init__(parent)
        self.resize(650, 450)
        self.setWindowTitle(version())
        
        self.text_area = QtGui.QTextBrowser()
 
        central_widget = QtGui.QWidget()
        central_layout = QtGui.QHBoxLayout()
        central_layout.addWidget(self.text_area)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        exit = QtGui.QAction(QtGui.QIcon('icons/exit.png'), 'Exit', self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip('Exit application')
        self.connect(exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

        self.statusBar()

        menubar = self.menuBar()
        file = menubar.addMenu('&File')
        file.addAction(exit)
        
        toolbar = self.addToolBar('Exit')
        toolbar.addAction(exit)
        
        #self.setGeometry(300, 300, 250, 150)
        #self.setWindowTitle('Icon')
        self.setWindowIcon(QtGui.QIcon('icons/logo.png'))

        self.count = 0
        
        self.start_threads()
        
    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            gl.qtflag = False
            while gl.dcflag == True:
                time.sleep(1)
            event.accept()
        else:
            event.ignore()
            
    def start_threads(self):
        self.threads = []              # this will keep a reference to threads
        thread = MyThread(self)    # create a thread
        thread.trigger.connect(self.update_text)  # connect to it's signal
        thread.start()             # start the thread
        self.threads.append(thread) # keep a reference
            
 
    def update_text(self, message):
        self.count += 1
        if self.count >1000:
            self.text_area.clear()
            self.count = 0
        self.text_area.append(unicode(message, 'gbk'))
 
if __name__ == '__main__':
    myapp = singleinstance()
    if myapp.aleradyrunning():
        print version(),'已经启动!3秒后自动退出...'
        time.sleep(3)
        sys.exit(0)
        
    app = QtGui.QApplication(sys.argv)
 
    mainwindow = MainWindow()
    mainwindow.show()
    #print 'after show'
 
    sys.exit(app.exec_())
