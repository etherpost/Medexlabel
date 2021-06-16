#!/usr/bin/env python
# coding: utf-8

#http://nagyak.eastron.hu/doc/system-config-printer-libs-1.2.4/pycups-1.9.51/html/cups.Connection-class.html#cancelJob
#https://code.woboq.org/qt5/include/cups/ipp.h.html#ipp_jstate_e

import cups
from tempfile import mktemp
from time import sleep
import os
from datetime import datetime, timedelta
import sys
import glob
import subprocess
import ipaddress
import time
from numberPad import numberPopup
from subprocess import Popen, PIPE, run

#these are for the PyQT5. There is overlap and should be cleaned up.
#pyrcc5 resources.qrc -o resources_rc.py

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import QTime, QTimer, QEvent, QDateTime, QThread
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDesktopWidget, QTableWidgetItem

os.chdir('/home/pi/LabelPrinter')

#the pump.ui is the UI definition file. It is created via the QT Designer tool
Ui_MainWindow, QtBaseClass = uic.loadUiType('printer.ui')

#this is the main program class which is the UI. It is driven by PyQT5 processes and interacts with the pump.ui file for display


class CheckPrinterThread(QtCore.QThread):
    notifyProgress = QtCore.pyqtSignal(int, int)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.running = True
        self.printFile = ''
        self.copyCount = 0

        self.f = open("log.txt", "w")

# Set up CUPS
        self.conn = cups.Connection()

        # Create a new subscriber
        self.printerName = 'DYMO-LabelWriter-450'
        cups.setUser(self.printerName)
        print('Cups')

#        self.sub = Subscriber(self.conn)
        # Subscribe the callback
#        self.sub.subscribe(self.my_callback)#, [event.CUPS_EVT_JOB_CREATED])
#        sub.subscribe(self.stopPrint, [event.CUPS_EVT_JOB_COMPLETED,
#                            event.CUPS_EVT_JOB_STOPPED])
        data = ''

#        self.subscription = self.conn.createSubscription("/", events=['all'], time_interval=10)

    def my_callback(self, event):
         print('event.title, event.description')
         print(event.description)

    def run(self):
        jobFinished = True
        lastNotifySequenceNumber = 0

        while(self.running):
           if(self.printFile != ''):
             options = {'copies': str(self.copyCount)}
             self.printId = self.conn.printFile(self.printerName, self.printFile, "NUMILK Label", options)
             print('id {}'.format(self.printId))
#             self.sub.subscribe(self.my_callback)#, [event.CUPS_EVT_JOB_CREATED])
             self.printFile = ''

             self.notifyProgress.emit(0,0)
             jobFinished = False

           if(not jobFinished):
             found = False
             try:
                ret = self.conn.getNotifications([self.subscription])
                found = len(ret['events']) > 0
             except:
                found = False

             if(found):
              i = 0

              events = ret['events']

              for notifies in events:
               notifyText = ''
               printerState = ''
               jobState = ''
               notifySubscribedEvent = ''
               jobStateReasons = ''
               percentComple = 0
               printerStateChanged = ''
               page = 0

               notifySequenceNumber = notifies['notify-sequence-number']
               if(notifySequenceNumber > lastNotifySequenceNumber):
                  lastNotifySequenceNumber = notifySequenceNumber
               else:
                  continue

               for notify, value in notifies.items():
#                  print(notify)

                  if(notify == "notify-text"):
                    jobStateReasons = value
                  if(notify == "notify-text"):
                     notifyText = value
                  if(notify == "printer-state"):
                     printerState = value
                  if(notify == "job-state"):
                    jobState = value
                  if(notify == "notify-subscribed-event"):
                    notifySubscribedEvent = value
                    if(notifySubscribedEvent == 'printer-state-changed'):
                        printerStateChanged = value
                  if(notifySubscribedEvent == 'job-progress'):
                     if(jobStateReasons.startswith('Finished')):
                        jobFinished = True
                        self.notifyProgress.emit(100, -1)
                     if(not jobFinished):
                        p1 = jobStateReasons.split(',')
                        if(len(p1) > 1):
                           p0 = p1[0].split(' ')
                           if(len(p0) > 1):
                             page = int(p0[2])
                           p2 = p1[1].split('%')
                           if(len(p2) > 1):
                             percentComple = int(p2[0])
                             self.notifyProgress.emit(percentComple, page)

#               if(printerStateChanged != ''):
#                  print ('{} : {} : {} : {} : {}'.format(notifyText, printerState, jobState, notifySubscribedEvent, jobStateReasons))
                  self.f.write ('{}: {} : {} : {} : {} : {}\n'.format(page, notifyText, printerState, jobState, notifySubscribedEvent, jobStateReasons))
                  self.f.flush()
#               print('---------------------------------------------------------------------------------')
           sleep(0.1)

    def startPrint(self, text):
       self.printFile(self.printerName, text)
       print('print label {} on {}'.format(self.printerName))

    def stopPrint(self):
       self.printFile = ''
       print('print label stopped {}'.format(self.printerName))


    def stop(self):
        print('stop')
        self.running = False

class Validator(QtGui.QValidator):
    def validate(self, string, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos

class MyApp(QMainWindow):
    def rebootApp(self):
       os.system("sudo shutdown -r now")
       os._exit(1)

    def shutdownApp(self):
       os.system("sudo shutdown -h now")
       os._exit(1)

    def exitApp(self):
       os._exit(1)

    def __init__(self,):
        super(MyApp, self).__init__()

        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)
#        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint) 

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().screenGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.showMaximized()
        centerWidth = centerPoint.x() - self.ui.mainFrame.width()/2
        centerHeight = centerPoint.y() - self.ui.mainFrame.height()/2
        centerPoint = self.ui.mainFrame.frameGeometry().center() - QtCore.QRect(QtCore.QPoint(), self.ui.mainFrame.sizeHint()).center()
#        self.ui.mainFrame.move(centerWidth,centerHeight)

        if(not os.path.exists("debug.txt")):
           self.showFullScreen()

        self.ui.printBtn.clicked.connect(self.printLabel)
        self.ui.shutdownBtn.clicked.connect(self.shutdown)

        self.ui.goBackPage1Btn.clicked.connect(self.goBack)
        self.ui.setupBtn.clicked.connect(self.gotoSetup)

        self.ui.changeDateBtn.clicked.connect(self.dateClick)
        self.ui.changeTimeBtn.clicked.connect(self.timeClick)
        self.ui.expirationHoursBtn.clicked.connect(self.expirationClick)
        self.ui.saveSetupBtn.clicked.connect(self.saveSetupClick)


        self.changedDate = False
        self.newDate = datetime.now()

        self.copyCount = 1
        self.maxExpiration = 10
        self.expiration = 6
        try:
          f = open("printer.cfg", "r")
          line = f.readline()
          f.close()
          self.expiration = int(line)
          print('new expiration {}'.format(self.expiration))
        except Exception as ex:
          pass
        
#        self.ui.printBtn.setEnabled(False)

        self.setup()
        self.gotoSetup()

        self.label2Print = 'label.png'
        self.tempLabel = 'label.jpg'
        self.tempLabel = 'label.txt'

# Set up CUPS
        self.conn = cups.Connection()
        printers = self.conn.getPrinters()
#        for printer in printers:
#           print('{} {} '.format( printer, printers[printer]["device-uri"]))

        self.printerName = 'DYMO'
        cups.setUser(self.printerName)

        ip = self.getIP()
        fileTime = datetime.fromtimestamp(os.path.getmtime(__file__))
        version = 'V{} - {}'.format(fileTime.strftime("%m.%d.%Y"), ip)
        self.ui.versionLbl.setText(version)

        timer = QTimer(self)
        timer.timeout.connect(self.updateTime)
        timer.start(1000)

        self.statusTimer = QTimer(self)

        self.labelTimer = QTimer(self)
        self.labelTimer.timeout.connect(self.hideLabel)

        self.hourFormat = '24'
        self.ui.currentTimeHHLbl.setText("")
        self.ui.currentTimeColonLbl.setText("")
        self.ui.currentTimeMMLbl.setText("")
        self.ui.currentDateLbl.setText("")
        self.updateTime()

        self.monitorPrinter = CheckPrinterThread()
        self.ui.printProgressBar.setValue(0)
        self.monitorPrinter.notifyProgress.connect(self.onProgress)
        self.monitorPrinter.start()
        self.ui.printProgressBar.hide()
   
        self.ui.stackedWidget.setCurrentIndex(0)

    def saveSetupClick(self):
        print('save setup click')
        self.expiration = int(self.ui.expirationTxt.text())
        f = open("printer.cfg", "w")
        f.write(str(self.expiration))
        f.close()
        print(self.expiration)
        dt = '"' + self.ui.dateTxt.text() + ' ' + self.ui.timeTxt.text() + '"'
        print(dt)
#sudo date --set "2019-07-11 12:00:00"
        p = Popen(['sudo /bin/date --set ' + dt],close_fds=True, shell=True)
        print('Popen {}, {} {}'.format('/bin/date', '--set', dt))

        time.sleep(3) # give it a second to launch

        self.ui.stackedWidget.setCurrentIndex(0)

    def dateClick(self):
        thisCell = self.ui.dateTxt
        self.exPopup = numberPopup(self.ui.mainFrame, thisCell, '', True, False, self.callBackDateOnSubmit, True, "Argument 2")
        self.exPopup.setGeometry(self.ui.dateTxt.x() + self.ui.dateTxt.width()+5, self.ui.dateTxt.y(), 340, 300)
        self.exPopup.show()

    def timeClick(self):
        thisCell = self.ui.timeTxt
        self.exPopup = numberPopup(self.ui.mainFrame, thisCell, '', False, True, self.callBackTimeOnSubmit, True, "Argument 2")
        self.exPopup.setGeometry(self.ui.timeTxt.x() + self.ui.timeTxt.width()+5, self.ui.timeTxt.y(), 340, 300)
        self.exPopup.show()

    def expirationClick(self):
        thisCell = self.ui.expirationTxt
        self.exPopup = numberPopup(self.ui.mainFrame, thisCell, '', False, False, self.callBackExpirationOnSubmit, True, "Argument 2")
        self.exPopup.setGeometry(self.ui.expirationTxt.x() + self.ui.expirationTxt.width()+5, self.ui.expirationTxt.y(), 340, 300)
        self.exPopup.show()


    def callBackDateOnSubmit(self, arg1, arg2): 
        print("Function is called with args: %s & %s" % (arg1, arg2))
        try:
          self.newDate = datetime.strptime(arg2, '%m/%d/%Y')
          self.ui.dateTxt.setText(self.newDate.strftime('%m/%d/%Y'))
        except ValueError:
          print("Incorrect date format, should be DD/MM/YYYY")
          msg = QMessageBox()
          msg.setIcon(QMessageBox.Critical)
          msg.setText('The date is an incorrect date format, should be DD/MM/YYYY')
          msg.setWindowTitle("Date Input Error")
          msg.setStandardButtons(QMessageBox.Ok)
          retval = msg.exec_()

    def callBackTimeOnSubmit(self, arg1, arg2): 
        print("Function is called with args: %s & %s" % (arg1, arg2))
        try:
          self.newTime = datetime.strptime(arg2, '%H:%M')
          self.ui.timeTxt.setText(self.newTime.strftime('%H:%M'))
        except ValueError:
          print("Incorrect time format, should be H:S")
          msg = QMessageBox()
          msg.setIcon(QMessageBox.Critical)
          msg.setText('The time is an incorrect time format, should be H:S')
          msg.setWindowTitle("Time Input Error")
          msg.setStandardButtons(QMessageBox.Ok)
          retval = msg.exec_()

    def callBackExpirationOnSubmit(self, arg1, arg2): 
        print("Function is called with args: %s & %s" % (arg1, type(arg2)))
        expiration = self.expiration
        oldValue = self.ui.expirationTxt.text()
        if(arg1):
           expiration = int(arg2)
           print(expiration)
           if(expiration > self.maxExpiration):
             msg = QMessageBox()
             msg.setIcon(QMessageBox.Critical)
             msg.setText('The length of the Expiration[{}] cannot be greater than {}'.format(expiration, self.maxExpiration))
             msg.setWindowTitle("Expiration Length Problem")
             msg.setStandardButtons(QMessageBox.Ok)
             retval = msg.exec_()
             return
           self.ui.expirationTxt.setText(arg2)


    def goBack(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def gotoSetup(self):
        dt = QDateTime.currentDateTime()
        time = QTime.currentTime()
        self.ui.dateTxt.setText(dt.toString('M/d/yyyy'))
        self.ui.timeTxt.setText(time.toString('hh:mm'))

        self.ui.stackedWidget.setCurrentIndex(1)

        self.ui.expirationTxt.setText(str(self.expiration))

        self.ui.expirationDateLbl.hide()
        self.ui.expirationTimeLbl.hide()
        self.ui.thisMedicationLbl.hide()

    def updateTime(self):
        dt = QDateTime.currentDateTime()
        textDT = dt.toString('dddd, MMMM d').upper()
        time = QTime.currentTime()
        textHH = time.toString('HH:mm:ss ap').split(' ')[0]
        textMM = time.toString('mm')
        textSS = time.toString('s')
        textPM = ''
        text = ' '
        if (time.second() % 2) == 0:
            text = ':'
        if(self.hourFormat == '12'):
           textPM = time.toString('AP')
           textTime = time.toString('h:mm ap').split(' ')[0]
        else:
           textTime = time.toString('h:mm').split(' ')[0]
        textTime = textTime.replace(":", text)

        self.ui.currentTimeHHLbl.setText(textHH)
        self.ui.currentTimeColonLbl.setText(text)
        self.ui.currentTimeMMLbl.setText(textMM)
        self.ui.currentDateLbl.setText(textDT)

        self.expirationTime = dt.addSecs(self.expiration * 60 * 60)
        self.ui.expirationLbl.setText(self.expirationTime.toString('M/d/yyyy h:mm'))
        self.ui.expirationDateLbl.setText('Expires ' + self.expirationTime.toString('M/d/yyyy'))
        self.ui.expirationTimeLbl.setText('at ' + self.expirationTime.toString('h:mm'))

    def resetDate(self):
        self.ui.askDateWidget.show()
        print('resetdate')

    def saveDate(self, qDate):
        self.newDate = qDate
        self.ui.dateTimeLbl.setText('{0}/{1}/{2}'.format(qDate.month(), qDate.day(), qDate.year()))
        self.changedDate = True
        self.ui.calendarWidget.hide()

    def changeDate(self):
#        dt = self.ui.dateTimeEdit.dateTime()
#        print(type(dt))
#        dtString = dt.toString(self.ui.dateTimeEdit.displayFormat())
#        print(dt, dtString)
#        self.ui.dateTimeLbl.setText(dtString)

        self.ui.calendarWidget.show()

    def dateOK(self):
#sudo date --set "2019-07-11 12:00:00"
        if(self.changedDate):
          try:
            subprocess.call(['sudo', 'date', '-s', '{:}'.format(self.newDate.toString('yyyy/MM/dd'))]) #Sets system time (Requires root, obviously)
            subprocess.call(['date'])
          except Exception as ex:
            print(str(ex))

        self.ui.askDateWidget.hide()

    def onProgress(self, percent, page):
        self.ui.printProgressBar.setValue(percent)
        if(page >= 0):
           self.ui.copyPrintedTxt.setText(str(page))

    def goBack(self):
        self.ui.stackedWidget.setCurrentIndex(0)

    def setup(self):
        font = QtGui.QFont("Basis Grotesque Pro", 14)

    def shutdown(self):
        if(os.path.exists("debug.txt")):
           self.exitApp()
        print('shutdown')
        self.shutdownApp()

    def callBackOnSubmit(self, arg1, arg2):
        copies = int(self.ui.copyCountTxt.text())
        if(copies <= 0):
           print('bad copies')
           self.ui.copyCountTxt.setText('')

    def hideLabel(self):

        self.ui.expirationDateLbl.hide()
        self.ui.expirationTimeLbl.hide()
        self.ui.thisMedicationLbl.hide()

    def addLabelText(self, labelPath):

        f = open(self.tempLabel, "w")
        f.write("\nThis Medication\n")
        f.write("Expires " + self.expirationTime.toString('M/d/yyyy') + '\n')
        f.write('at ' +self.expirationTime.toString('H:mm') + '\n')
        f.close()
        return

        yPos = 0
        xPos = 0
        xLen = 97
        yLen = 77

        pen = QPen(QtCore.Qt.black)
        pen.setWidth(2)

        font = QFont()
        font.setFamily('Arial')
        font.setBold(True)
        font.setPointSize(12)

        # convert image file into pixmap
        labelPixmap = QtGui.QPixmap(self.label2Print)

        # create painter instance with pixmap
        labelPainterInstance = QtGui.QPainter(labelPixmap)
#        labelPainterInstance.drawPixmap(xPos, yPos, labelPixmap)
#        labelPainterInstance.rotate(90)
        labelPainterInstance.drawText(10, 10, "Expiration ")
        labelPainterInstance.setFont(font)
        expires = (datetime.today() + timedelta(hours=7)).strftime('%m/%d/%Y')
        labelPainterInstance.drawText(10, 200, expires)

        labelPainterInstance.drawText(10, -150, "This Medication")
        labelPainterInstance.drawText(10, -100, "Expires")
        labelPainterInstance.drawText(10, -50, self.expirationTime.toString('M/d/yyyy'))
        labelPainterInstance.drawText(10, -20, self.expirationTime.toString('h:mm'))

        labelPainterInstance.end()

        labelPixmap.save(self.tempLabel)

    def printLabel(self):

        self.ui.expirationDateLbl.show()
        self.ui.expirationTimeLbl.show()
        self.ui.thisMedicationLbl.show()
        self.labelTimer.start(1000 *3)

        self.copyCount = 1

        self.addLabelText(self.label2Print)

# Send the picture to the printer
        f = os.path.abspath(self.tempLabel)

        options = {'copies': str(self.copyCount)}

        try:
           self.printId = self.conn.printFile(self.printerName, f, "Expiration Label", options)

        except Exception as ex:
           print('printer failure {}'.format(str(ex)))
#           self.ui.printBtn.setEnabled(False)
           return
           msg = QMessageBox()
           msg.setIcon(QMessageBox.Critical)
           msg.setText(str(ex))
           msg.setWindowTitle("Printer Problem")
           msg.setStandardButtons(QMessageBox.Ok)
           retval = msg.exec_()

           return


    def getIP(self):
       import socket

       s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
       except Exception:
        IP = ''
       finally:
        s.close()

       print(IP)
       return IP

def main():
  print(' >>> {} {}'.format(datetime.now(), 'app started'))

  pid = os.getpid()

  app = QApplication(sys.argv)

#start the UI. Pass the scale thread to it so the emit/signal to work
  window = MyApp()

  app.exec_()
#should never get here unless we are done.
  os._exit(0)
  
if __name__ == '__main__':

  try:
    main()
  except Exception as e:
    print(str(e))



# Wait until the job finishes
#while conn.getJobs().get(print_id, None):
#    sleep(1)
#unlink(output)
