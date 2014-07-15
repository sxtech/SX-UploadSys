from dataclient import DataClient
from PyQt4 import QtGui, QtCore
import sys,time,datetime,os
import MySQLdb
import logging
import logging.handlers
#from helpfunc import HelpFunc
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
                    level    = logging.WARNING,
                    format   = '%(asctime)s %(filename)s[line:%(lineno)d] [%(levelname)s] %(message)s',
                    datefmt  = '%Y-%m-%d %H:%M:%S',
                    filename = logFilename,
                    filemode = 'a');

def version():
    return 'SX-UploadSys V1.0.2'

 
class MyThread(QtCore.QThread):
    trigger = QtCore.pyqtSignal(str)
 
    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent)
 
    def run(self):
        gl.TRIGGER = self.trigger
        m = dcmain(self.trigger)
        m.mainloop()

class dcmain:
    def __init__(self,trigger):

        initLogging(r'log\uploadsys.log')

        gl.TRIGGER.emit("<font size=6 font-weight=bold face=arial color=tomato>%s</font>"%('Welcome to use '+version()))
        self.dc = DataClient()

    def __del__(self):
        del self.dc

    def mainloop(self):
        self.dc.main()
    
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
            gl.QTFLAG = False
            while gl.DCFLAG == True:
                time.sleep(1)
            event.accept()
        else:
            event.ignore()
            
    def start_threads(self):
        self.threads = []              # this will keep a reference to threads
        thread = MyThread(self)        # create a thread
        thread.trigger.connect(self.update_text)  # connect to it's signal
        thread.start()                 # start the thread
        self.threads.append(thread)    # keep a reference         
 
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
