#!/usr/bin/env python

'''@package docstring
CiliaC - A peak tracking program for Nuclear Medicine images
Created on 21/12/2013
@author: Mark Pearson

'''
from __future__ import print_function

from dicomdata import DicomInfo
from cplots import *
from cdisplay import ImageDisplay
from cdata import CiliaData
#from trackingpoints import TrackingPoints
from imageView import ImageView
from cgui import Ui_CiliaC

import sys
import os.path
import struct
from PyQt4 import QtCore, QtGui
import copy
import csv
from set_limits import Ui_DualSpin
from functools import partial
import numpy as np
from scipy import ndimage, stats
import ConfigParser
import logging
import pickle
import dicom
import datetime
from tempfile import mkdtemp
from shutil import rmtree
from UserDict import UserDict

'''The following section is necessary for py2exe to create an executable on windws'''
from pyqtgraph.graphicsItems import TextItem
def dependencies_for_myprogram():
    from scipy.sparse.csgraph import _validation

from ctypes import util
try:
    from OpenGL.platform import win32
except AttributeError:
    pass

from debugging import *

class StartQT4(QtGui.QMainWindow):
  '''GUI control class
  '''
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)
    #self.conf = Initialization()
    self.conf = LoadDefaults('ciliac.cfg')
    self.conf['dcmName'] = None
    #print(self.conf)
    self.ui = Ui_CiliaC()
    self.ui.setupUi(self)
    self.graphicsViews = {}
    self.imageViews = []
    self.imageViewList = []
    self.imageViewDict = {}
    self.dummyview = ImageView(self.ui, self.conf, "Dummy")
    #self.filename = None
    #self.filenames = None
    self.sumData = None
    self.summedSens = 4
    self.imgIndex = 0
    self.firstFrame = 0
    self.lastFrame = 0
    self.latAngle = 0.0
    self.isSummedImage = False
    self.isAnimated = False
    self.comPlotFlag = False
    self.overridePixelSize = 1.0
    self.overridePixelFlag = False
    self.win3d = gl.GLViewWidget()
    self.winPlot = None
    #self.winPlot =  pg.GraphicsLayoutWidget()
    self.is3dPloted = False
    self.measurementUnits = 'fr'
    #self.resultsDir = "."
    self.gpl = None
    self.lpl = None
    self.mpl = None
    self.loadingFlag = False
    self.currentOperation = None
    #self.vhpl = None
    #self.trackType = 'No_ROI'
    self.trackManualFlag = False
    self.trackManualType = 'Movement'
    self.timer = QtCore.QTimer()
    self.statusLeft = QtGui.QLabel('Load a file to begin')
    self.statusLeft.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
    self.statusMiddle = QtGui.QLabel('')
    self.statusMiddle.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
    self.statusRight = QtGui.QLabel('')
    self.statusRight.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
    #self.imgStatus = QtGui.QLabel('0,0:0')
    self.ui.statusbar.addWidget(self.statusLeft, 1)
    self.ui.statusbar.addWidget(self.statusMiddle, 1)
    self.ui.statusbar.addWidget(self.statusRight, 1)
    self.setupProgressLog()
    self.setDefaults()
    self.setShowOverlays()
    self.setMeasurementUnits(self.measurementUnits)
    import csummary
    
    QtCore.QObject.connect(self,QtCore.SIGNAL("refreshDisplay"), self.refreshDisplay)
    QtCore.QObject.connect(self,QtCore.SIGNAL("refreshPlots"), self.refreshPlots)
# File
    QtCore.QObject.connect(self.ui.buttonRotateLeft,QtCore.SIGNAL("clicked()"), self.rotateData90)
    QtCore.QObject.connect(self.ui.buttonRotateRight,QtCore.SIGNAL("clicked()"), self.rotateData90)

    QtCore.QObject.connect(self.ui.actionLoad_Dicom_File,QtCore.SIGNAL("triggered()"), self.fileOpenDialog)
    QtCore.QObject.connect(self.ui.buttonLoadFile,QtCore.SIGNAL("clicked()"), self.fileOpenDialog)

    QtCore.QObject.connect(self.ui.actionSave_Dicom_File,QtCore.SIGNAL("triggered()"), self.fileSaveDialog)
    QtCore.QObject.connect(self.ui.buttonSaveFile,QtCore.SIGNAL("clicked()"), self.fileSaveDialog)
#Image
    QtCore.QObject.connect(self.ui.actionDICOM_Info,QtCore.SIGNAL("triggered()"), self.showDicomInfo)
    QtCore.QObject.connect(self.ui.actionRotate_90_Deg_Left,QtCore.SIGNAL("triggered()"), self.rotateData90)
    QtCore.QObject.connect(self.ui.actionRotate_90_Deg_Right,QtCore.SIGNAL("triggered()"), self.rotateData90)
    QtCore.QObject.connect(self.ui.actionRotate_Set_Lateral_Angle,QtCore.SIGNAL("triggered()"), self.setLateralAngle)
    QtCore.QObject.connect(self.ui.actionRotate_Using_ROI,QtCore.SIGNAL("triggered()"), self.rotateUsingROI)
    QtCore.QObject.connect(self.ui.actionSmooth,QtCore.SIGNAL("triggered()"), self.smoothData)
    QtCore.QObject.connect(self.ui.buttonSmooth,QtCore.SIGNAL("clicked()"), self.smoothData)
    QtCore.QObject.connect(self.ui.actionScale,QtCore.SIGNAL("triggered()"), self.scaleData)
    QtCore.QObject.connect(self.ui.actionRemove_Background,QtCore.SIGNAL("triggered()"), self.removeBackground)
    QtCore.QObject.connect(self.ui.actionApply_Mask,QtCore.SIGNAL("triggered()"), self.maskFrames)
    #QtCore.QObject.connect(self.ui.actionImageWindow,QtCore.SIGNAL("triggered()"), self.adjustView1BrightnessContrast)

    QtCore.QObject.connect(self.ui.actionXYPlots,QtCore.SIGNAL("triggered()"), self.plotCentreOfMass)
    QtCore.QObject.connect(self.ui.buttonVHPlot,QtCore.SIGNAL("clicked()"), self.plotCentreOfMass)
    QtCore.QObject.connect(self.ui.actionClose_Plots,QtCore.SIGNAL("triggered()"), self.removePlots)
    QtCore.QObject.connect(self.ui.buttonCentreOfMass,QtCore.SIGNAL("clicked()"), self.trackAuto)
    QtCore.QObject.connect(self.ui.buttonRedraw,QtCore.SIGNAL("clicked()"), self.refreshDisplay)
    QtCore.QObject.connect(self.ui.buttonPrevImage,QtCore.SIGNAL("clicked()"), self.showPrevFrame)
    QtCore.QObject.connect(self.ui.buttonNextImage,QtCore.SIGNAL("clicked()"), self.showNextFrame)
    QtCore.QObject.connect(self.ui.buttonAnimateStart,QtCore.SIGNAL("clicked()"), self.animateStartStop)
    QtCore.QObject.connect(self.ui.buttonRender,QtCore.SIGNAL("clicked()"), self.togglePlot3d)
    QtCore.QObject.connect(self.ui.buttonSummedImage,QtCore.SIGNAL("clicked()"), self.toggleSummedImage)
    QtCore.QObject.connect(self.ui.radioButtonFrames,QtCore.SIGNAL("clicked()"), self.changeUnits)
    QtCore.QObject.connect(self.ui.radioButtonTime,QtCore.SIGNAL("clicked()"), self.changeUnits)
    QtCore.QObject.connect(self.ui.actionPrint_Virt,QtCore.SIGNAL("triggered()"), self.printVirtical)
    QtCore.QObject.connect(self.ui.actionPrint_Horiz,QtCore.SIGNAL("triggered()"), self.printLateral)
    QtCore.QObject.connect(self.ui.actionStraighten,QtCore.SIGNAL("triggered()"), self.straighten)
    QtCore.QObject.connect(self.ui.actionExport,QtCore.SIGNAL("triggered()"), self.exportPlotData)
    QtCore.QObject.connect(self.ui.buttonSaveAsCSV,QtCore.SIGNAL("clicked()"), self.exportPlotData)
    QtCore.QObject.connect(self.ui.buttonShowOverlays,QtCore.SIGNAL("clicked()"), self.setShowOverlays)
    QtCore.QObject.connect(self.ui.spinFrom,QtCore.SIGNAL("valueChanged(int)"), self.setAnalysisLimits)
    QtCore.QObject.connect(self.ui.spinTo,QtCore.SIGNAL("valueChanged(int)"), self.setAnalysisLimits)
    QtCore.QObject.connect(self.ui.actionVelocity_Limits,QtCore.SIGNAL("triggered()"), self.setVelocityLimits)
    QtCore.QObject.connect(self.ui.actionCalcVelocity,QtCore.SIGNAL("triggered()"), self.calculateVelocity)
    QtCore.QObject.connect(self.ui.buttonCalcVelocity,QtCore.SIGNAL("clicked()"), self.calculateVelocity)
    QtCore.QObject.connect(self.ui.actionAdd_Mask,QtCore.SIGNAL("triggered()"), self.addMaskROI)
    QtCore.QObject.connect(self.ui.actionMask_Frames,QtCore.SIGNAL("triggered()"), self.addMaskROI)
    QtCore.QObject.connect(self.ui.actionRemove_Mask,QtCore.SIGNAL("triggered()"), self.removeMaskROI)
    QtCore.QObject.connect(self.ui.actionAdd_ROI,QtCore.SIGNAL("triggered()"), self.addTrackingROI)
    QtCore.QObject.connect(self.ui.actionDelete_ROI,QtCore.SIGNAL("triggered()"), self.removeTrackingROI)
    QtCore.QObject.connect(self.ui.radioCOMFrame,QtCore.SIGNAL("clicked()"), self.changeTracking)
    QtCore.QObject.connect(self.ui.radioCOMInside,QtCore.SIGNAL("clicked()"), self.changeTracking)
    QtCore.QObject.connect(self.ui.radioCOMPeak,QtCore.SIGNAL("clicked()"), self.changeTracking)
    QtCore.QObject.connect(self.ui.actionReset_Limits,QtCore.SIGNAL("triggered()"), self.resetCOMLimits)
    QtCore.QObject.connect(self.ui.actionSet_Animation_Speed,QtCore.SIGNAL("triggered()"), self.setAnimationDelay)
    QtCore.QObject.connect(self.ui.actionSet_Summed_Sensitivity,QtCore.SIGNAL("triggered()"), self.setSummedSensitivity)
    QtCore.QObject.connect(self.ui.actionAnalyse_Calibration_Image,QtCore.SIGNAL("triggered()"), self.analyseCalibrationImage)
    QtCore.QObject.connect(self.ui.actionSummary,QtCore.SIGNAL("triggered()"), partial(csummary.makeSummary, 'BOTH'))
    QtCore.QObject.connect(self.ui.buttonSaveReport,QtCore.SIGNAL("clicked()"), partial(csummary.makeSummary, 'BOTH'))
    QtCore.QObject.connect(self.ui.actionReport_Both,QtCore.SIGNAL("triggered()"), partial(csummary.makeSummary, 'BOTH'))
    QtCore.QObject.connect(self.ui.actionReport_Anterior,QtCore.SIGNAL("triggered()"), partial(csummary.makeSummary, 'ANT'))
    QtCore.QObject.connect(self.ui.actionReport_Lateral,QtCore.SIGNAL("triggered()"), partial(csummary.makeSummary, 'LAT'))
    QtCore.QObject.connect(self.ui.actionTrackThreshold,QtCore.SIGNAL("triggered()"), self.setTrackingThreshold)
    QtCore.QObject.connect(self.ui.action3dZ_scale,QtCore.SIGNAL("triggered()"), self.set3dZScale)
    QtCore.QObject.connect(self.ui.actionHelpAbout,QtCore.SIGNAL("triggered()"), self.showHelpAbout)
    QtCore.QObject.connect(self.ui.actionMeasure_Size_Inside_ROI,QtCore.SIGNAL("triggered()"), self.measureSizeInsideROI)
    QtCore.QObject.connect(self.ui.actionSetLogInfo,QtCore.SIGNAL("triggered()"), partial(self.setLogLevel, 0))
    QtCore.QObject.connect(self.ui.actionSetLogWarning,QtCore.SIGNAL("triggered()"), partial(self.setLogLevel, 1))
    QtCore.QObject.connect(self.ui.actionSetLogDebug,QtCore.SIGNAL("triggered()"), partial(self.setLogLevel, 2))
    QtCore.QObject.connect(self.ui.actionSetPixel_Size,QtCore.SIGNAL("triggered()"), self.setPixelSize)
    QtCore.QObject.connect(self.ui.view1BCAutoCheckbox,QtCore.SIGNAL("clicked()"), partial(self.setBCAuto, 1))
    QtCore.QObject.connect(self.ui.view2BCAutoCheckbox,QtCore.SIGNAL("clicked()"), partial(self.setBCAuto, 2))
    QtCore.QObject.connect(self.ui.actionMeasureROI_Position,QtCore.SIGNAL("triggered()"), self.showROIPos)
    QtCore.QObject.connect(self.ui.actionTrack_ISO_Add,QtCore.SIGNAL("triggered()"), self.addIsocurveROI)
    QtCore.QObject.connect(self.ui.actionTrack_ISO_Display,QtCore.SIGNAL("triggered()"), self.showIsocurveValues)
    QtCore.QObject.connect(self.ui.actionTrack_ISO_Threshold,QtCore.SIGNAL("triggered()"), self.isocurveThreshold)
    QtCore.QObject.connect(self.ui.actionTrackMovement_Start,QtCore.SIGNAL("triggered()"), partial(self.trackingStart, 'Movement'))
    QtCore.QObject.connect(self.ui.actionTrackMovement_Stop,QtCore.SIGNAL("triggered()"), self.trackingStop)
    QtCore.QObject.connect(self.ui.actionTrackSpiral_Start,QtCore.SIGNAL("triggered()"), partial(self.trackingStart, 'Spiral'))
    QtCore.QObject.connect(self.ui.actionTrackSpiral_Stop,QtCore.SIGNAL("triggered()"), self.trackingStop)
    QtCore.QObject.connect(self.ui.actionManual_COM,QtCore.SIGNAL("triggered()"), partial(self.setManualType, 'Movement'))
    QtCore.QObject.connect(self.ui.actionManual_Spiral,QtCore.SIGNAL("triggered()"), partial(self.setManualType, 'Spiral'))
    QtCore.QObject.connect(self.ui.actionManual_Start,QtCore.SIGNAL("triggered()"), self.trackManualStart)
    QtCore.QObject.connect(self.ui.actionManual_Stop,QtCore.SIGNAL("triggered()"), self.trackManualStop)
    QtCore.QObject.connect(self.ui.actionManual_Clear,QtCore.SIGNAL("triggered()"), self.trackManualClear)
    QtCore.QObject.connect(self.ui.actionManual_Plot,QtCore.SIGNAL("triggered()"), self.trackManualPlot)
    QtCore.QObject.connect(self.ui.actionManual_Calc_Velocity,QtCore.SIGNAL("triggered()"), self.trackManualCalcVelocity)
    QtCore.QObject.connect(self.ui.actionView_No_ROI,QtCore.SIGNAL("triggered()"), partial(self.trackView, 'No_ROI'))
    QtCore.QObject.connect(self.ui.actionView_Fixed_ROI,QtCore.SIGNAL("triggered()"), partial(self.trackView, 'Fixed_ROI'))
    QtCore.QObject.connect(self.ui.actionView_Moving_ROI,QtCore.SIGNAL("triggered()"), partial(self.trackView, 'Moving_ROI'))
    QtCore.QObject.connect(self.ui.actionView_Movement,QtCore.SIGNAL("triggered()"), partial(self.trackView, 'Movement'))
    QtCore.QObject.connect(self.ui.actionView_Spiral,QtCore.SIGNAL("triggered()"), partial(self.trackView, 'Spiral'))
    #QtCore.QObject.connect(self.ui.actionTrackMovingROI_Active,QtCore.SIGNAL("triggered()"), self.trackROIPeak)

    QtCore.QObject.connect(self.ui.buttonProcessProceed,QtCore.SIGNAL("clicked()"), self.doProcessProceed)
    QtCore.QObject.connect(self.ui.buttonProcessCancel,QtCore.SIGNAL("clicked()"), self.doProcessCancel)

    self.allButtons = {
      'graphing': ['buttonVHPlot'],
      'saving': ['buttonSaveFile', 'buttonSaveReport'],
      'savecsv': ['buttonSaveAsCSV'],
      'manipulation': ['buttonCentreOfMass', 'buttonRotateLeft', 'buttonRotateRight', 'buttonRender'],
      'animate' : ['buttonPrevImage', 'buttonNextImage', 'buttonAnimateStart', 'buttonRedraw'],
      'calculateItems' : ['buttonCalcVelocity'],
      'loadedItems' : ['spinFrom', 'spinTo', 'buttonSummedImage', 'buttonSmooth'],
      'menuViews' : ['actionView_No_ROI', 'actionView_Fixed_ROI', 'actionView_Moving_ROI', 'actionView_Movement', 'actionView_Spiral']
      }
    self.setButtonsAndMenus('Reset')
    self.disableItems(['buttonProcessProceed', 'buttonProcessCancel', 'animDelaySlider'], True)
    #self.graphButtons = ['buttonVHPlot']
    #self.manipButtons = ['buttonCentreOfMass', 'buttonRotateLeft', 'buttonRotateRight', 'buttonRender']
    #self.animateButtons = ['buttonPrevImage', 'buttonNextImage', 'buttonAnimateStart', 'buttonRedraw']
    #self.calculateItems = ['buttonCalcVelocity']
    #self.loadedItems = ['spinFrom', 'spinTo', 'buttonSummedImage', 'buttonSmooth']
    #self.disableItems(self.graphButtons+self.manipButtons+self.animateButtons+self.loadedItems+self.calculateItems)
    #self.hideElement('buttonProcessProceed')
    #self.hideElement('buttonProcessCancel')

  def showHelpAbout(self):
    QtGui.QMessageBox.about(self, "About Ciliac", 
"""
Trans Mucocillory Velocity Calculator
Copyright 2014 Sydney local Health District

   For further information contact:
   Mark Pearson
   Department of Nuclear Medicine
   Concord Hospital, Sydney
   (Mark.Pearson@sswahs.nsw.gov.au)
""")

  def setAccessibleName(self, name):
    pass

  def mousePressEvent(self, event):
    logger.debug('StartQT4::mousePressEvent()')
    for iv in self.imageViews:
      if self.trackManualFlag == True:
        iv.addManualTrackPoint()
      else:
        iv.addDummyTrackPoint()
    #print("mb")

  def keyPressEvent(self, event):
    if int(event.modifiers()) == (QtCore.Qt.ControlModifier):
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_F :
        self.showFrame(self.ui.spinFrom.value())
        self.ui.imageSlider.setValue(self.imgIndex)
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_T :
        self.showFrame(self.ui.spinTo.value())
        self.ui.imageSlider.setValue(self.imgIndex)
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_Left :
        self.showFirstFrame()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_Right :
        self.showLastFrame()
    else:
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_A :
        self.animateStartStop()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_D :
        self.measurePixelSize()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_F :
        self.ui.spinFrom.setProperty("value", self.imgIndex)
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_T :
        self.ui.spinTo.setProperty("value", self.imgIndex)
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_C :
        self.trackAuto()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_L :
        self.fileOpenDialog()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_M :
        if self.trackManualFlag:
          self.trackManualStop()
        else:
          self.trackManualStart()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_P :
        self.removePlots()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_V :
        self.setVelocityLimits()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_Left :
        self.showPrevFrame()
      if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_Right :
        self.showNextFrame()
    self.setAnalysisLimits()

  def setButtonsAndMenus(self, task, item=None):
    logger.debug('StartQT4::setButtonsAndMenus(%s)' % task)
    blist = []
    if task == 'Reset':
      self.ui.view1BCAutoCheckbox.setChecked(True)
      self.ui.view2BCAutoCheckbox.setChecked(True)
      for v1 in self.allButtons.values():
        for v2 in v1:
          blist.append(v2)
      self.disableItems(blist)
    if task == 'FileLoaded':
      for v1 in (self.allButtons['manipulation'], self.allButtons['saving'], self.allButtons['animate'], self.allButtons['loadedItems']):
        for v2 in v1:
          blist.append(v2)
      self.enableItems(blist)
    if task == 'CalcCOM':
      for v1 in (self.allButtons['graphing'], self.allButtons['calculateItems'], self.allButtons['savecsv']):
        for v2 in v1:
          blist.append(v2)
      self.enableItems(blist)
      if item is not None:
        self.enableItems(['actionView_'+item])
    if task == 'StartProcess':
      self.enableItems(['buttonProcessProceed', 'buttonProcessCancel'])
      self.showElement('buttonProcessProceed')
      self.showElement('buttonProcessCancel')
      for v1 in self.allButtons.values():
        for v2 in v1:
          blist.append(v2)
      self.disableItems(blist)
      if self.currentOperation == 'MASK':
        self.enableItems(self.allButtons['animate'])
    if task == 'StopProcess':
      self.disableItems(['buttonProcessProceed', 'buttonProcessCancel'], True)
      for v1 in (self.allButtons['manipulation'], self.allButtons['saving'], self.allButtons['animate'], self.allButtons['loadedItems']):
        for v2 in v1:
          blist.append(v2)
      self.enableItems(blist)

  def setLogLevel(self, l):
    if l == 0:
      logger.setLevel(logging.INFO)
    if l == 1:
      logger.setLevel(logging.WARN)
    if l == 2:
      logger.setLevel(logging.DEBUG)

  def disableItems(self, blist, hide=False):
    '''Disable selected buttons and menu entries
    '''
    for b in blist:
      getattr(self.ui, b).setEnabled(False)
      if hide:
        self.hideElement(b)
    #self.ui.buttonVHPlot.setEnabled(False)
    
  def enableItems(self, blist):
    '''Enable selected buttons and menu entries
    '''
    for b in blist:
      getattr(self.ui, b).setEnabled(True)
    #self.ui.buttonVHPlot.setEnabled(True)

  def hideElement(self, e):
    getattr(self.ui, e).setVisible(False)

  def hideElements(self, elist):
    for e in elist:
      getattr(self.ui, e).setVisible(False)

  def showElements(self, elist):
    for e in elist:
      self.showElement(e)

  def showElement(self, e):
    getattr(self.ui, e).setVisible(True)

  def setDefaults(self):
    self.measurementUnits = self.conf['Units']
    #self.animateDelay = self.conf['AnimSpeed']
    #self.hidepatientid = self.conf['HidePatientID']
    #self.trackType = self.conf['Tracking']
    self.changeTracking(self.conf['Tracking'])
    self.setMeasurementUnits(self.measurementUnits)
    #self.resultsDir = self.conf['ResultsDir']
    
  def closeEvent(self, event):
    '''Close any sub-windows and exit
    '''
    logger.debug('StartQT4::closeEvent()')
    print('closeEvent')
    for iv in self.imageViews:
      iv.closeAllPlots()
    if self.is3dPloted:
      self.gpl.closeWindow()
    #QtGui.QApplication.quit()
    event.accept()
    
  def setupProgressLog(self):
    '''Set font, size etc for progress log
    '''
    self.ui.progressLog.setReadOnly(True)
    self.ui.progressLog.setLineWrapMode(QtGui.QTextEdit.NoWrap)
    font = self.ui.progressLog.font()
    font.setFamily("Courier")
    font.setPointSize(10)
    
  def updateProgressLog(self, msg):
    '''Add entry to progress log
    '''
    self.ui.progressLog.append(msg)

  def setMeasurementUnits(self, mode):
    '''Update UI for either frames or mm
    '''
    logger.debug('StartQT4::setMeasurementUnits(%s)' % mode)
    if mode == 'fr':
      self.ui.radioButtonFrames.setChecked(True)
      self.ui.radioButtonTime.setChecked(False)
    if mode == 'mm':
      self.ui.radioButtonFrames.setChecked(False)
      self.ui.radioButtonTime.setChecked(True)
    for iv in self.imageViews:
      iv.setMeasurementUnits(self.measurementUnits)
    self.emit(QtCore.SIGNAL("refreshPlots"))
    #if self.lpl is not None:
      #self.lpl.setMeasurementUnits(self.setMeasurementUnits)
    
  def changeUnits(self):
    '''Set units to either frames or mm. Update plots
    '''
    logger.debug('StartQT4::changeUnits()')
    if self.ui.radioButtonFrames.isChecked():
      self.measurementUnits = 'fr'
    if self.ui.radioButtonTime.isChecked():
      self.measurementUnits = 'mm'
    self.setMeasurementUnits(self.measurementUnits)

  def resetAll(self):
    '''Clear previous data when opening new files
    '''
    logger.debug('StartQT4::resetAll()')
    self.setButtonsAndMenus('Reset')
    #self.disableItems(self.graphButtons+self.manipButtons+self.animateButtons+self.loadedItems+self.calculateItems)
    self.imgIndex = 0
    self.ui.imageSlider.setValue(self.imgIndex)
    self.removeCOMPlot()
    self.removeCCOMPlot()
    if self.is3dPloted is True:
      self.togglePlot3d()
    for iv in self.imageViews:
      iv.resetAll()
    self.imageViews = []
    self.lastFrame = 0
    self.conf = LoadDefaults('ciliac.cfg')
    self.isSummedImage = False
    self.isAnimated = False
    self.latAngle = 0.0
    self.overridePixelSize = 1.0
    self.overridePixelFlag = False
    #self.trackType = 'No_ROI'
    self.changeTracking(self.conf['Tracking'])
    self.graphicsViews = {}
    #self.dispA.hideCom()

  def fileOpenDialog(self):
    '''GUI for choosing dicom file(s).
    '''
    fd = QtGui.QFileDialog(self)
    filenames = fd.getOpenFileNames(directory=self.conf['DataDir'], filter='Dicom Files *.dcm(*.dcm);;All Files *(*)')
    if len(filenames) == 0:
      return
    if len(filenames) > 2:
      QtGui.QMessageBox.information(self, "Too many files selected", "Only 2 files will be loaded")
      del filenames[2:]
    self.resetAll()
    self.conf['dcmName'] = filenames[0]
    if not os.path.isfile(self.conf['dcmName']):
      return
    self.conf['DataDir'] = os.path.dirname(str(self.conf['dcmName']))
    #print(self.conf['DataDir'])
    self.classifyFiles(filenames)
    for fname in filenames:
      self.loadDicom(fname)
    #head, tail = os.path.split('%s' % self.conf['dcmName'])
    #self.statusMiddle.setText(self.dcm[0].getPatientName(self.ds[0]))

  def classifyFiles(self, flist):
    if len(flist) == 1:
      self.graphicsViews[flist[0]] = 'view1GraphicsView'
      return
    info = {}
    views = {}
    pp = {}
    tp = {}
    index = 0
    for f in flist:
      ds = dicom.read_file(str(f))
      view = 'UNKNOWN'
      if ds.ImageID.lower().find('lateral') != -1:
        view = 'LAT'
      if ds.ImageID.lower().find('anterior') != -1:
        view = 'ANT'
      series = 'Unknown'
      if ds.SeriesDescription.lower().find('pre') != -1:
        series = 'Pre'
      if ds.SeriesDescription.lower().find('post') != -1:
        series = 'Post'
      d = ds.StudyDate
      t = ds.StudyTime
      studyDateTime = "%s-%s-%s %s:%s" % (d[0:4], d[4:6], d[6:8], t[0:2], t[2:4])
      dt = datetime.datetime.strptime(studyDateTime, "%Y-%m-%d %H:%M")
      dayTime = dt.strftime("%a %H:%m")
      label = '%s-%s %s' % (view, series, dayTime)
      views[view] = 1
      pp[series] = 1
      tp[d] = 1
      info[index] = {'file':f, 'view':view, 'series':series, 'time':d+t}
      index += 1
    #print(views, pp, tp)
    #print(info)
    self.graphicsViews[info[0]['file']] = 'view1GraphicsView'
    self.graphicsViews[info[1]['file']] = 'view2GraphicsView'
    if len(views) == 1 and len(pp) == 1:
      print(info[0]['file'], info[0]['time'])
      print(info[1]['file'], info[0]['time'])
    if len(views) == 1 and len(pp) == 2:
      if info[0]['series'] == 'Post':
        self.graphicsViews[info[0]['file']] = 'view2GraphicsView'
        self.graphicsViews[info[1]['file']] = 'view1GraphicsView'
    if len(views) == 2 and len(pp) == 1:
      if info[0]['view'] == 'LAT':
        self.graphicsViews[info[0]['file']] = 'view2GraphicsView'
        self.graphicsViews[info[1]['file']] = 'view1GraphicsView'
    del ds

  def loadDicom(self, fname):
    '''Update GUI after loading DICOM data 
    '''
    logger.info('Load %s' % fname)
    self.updateProgressLog('Load %s' % os.path.basename(str(fname)))
    view = ImageView(self.ui, self.conf, fname)
    view.addView(str(fname), self.graphicsViews[fname])
    vname = view.getViewShortName()
    if view.isValidDataset():
      self.loadingFlag = True
      self.imageViews.append(view)
      self.imageViewList.append((view, vname, True))
      self.imageViewDict[vname] = { 'class':view, 'active':True}
      #self.lastFrame = self.imageViews[-1].getLastFrame()
      self.firstFrame = 0
      self.lastFrame = view.getLastFrame()
      self.ui.imageSlider.setMinimum(0)
      self.ui.imageSlider.setMaximum(self.lastFrame)
      self.ui.imageSlider.valueChanged.connect(self.showFrame)
      #(iMin, iMax) = view.getImageMinMax()
      #self.setBCSlider(vname, iMin, iMax)
      self.setBCSlider(view)
      self.resetCOMLimits(0, self.lastFrame)
      if view.isPrimaryDataset() and self.ui.actionSet_Preprocess_image_on_Load.isChecked():
        self.rotateData90(self.conf['Rotate'], self.imageViews[-1])
        if self.conf['RemoveBackground']:
          self.removeBackground(view)
        if self.conf['Smooth']:
          self.smoothData(view)
      self.setAnalysisLimits()
      self.emit(QtCore.SIGNAL("refreshDisplay"))
      self.statusLeft.setText(self.imageViews[0].getConversions())
      self.statusMiddle.setText(self.imageViews[0].getNameAndSeries(self.conf['HidePatientID']))
      if len(self.imageViews) > 1:
        self.statusRight.setText(self.imageViews[1].getNameAndSeries(self.conf['HidePatientID']))
      self.setButtonsAndMenus('FileLoaded')
      self.loadingFlag = False
      view.loadMetadata()
      self.setTrackingViewStatus(view.getActiveTracking())
      label = view.getViewLabel()
      #self.enableItems(self.manipButtons+self.animateButtons+self.loadedItems)
    else:
      self.updateProgressLog('Unsupported DICOM image')

  def fileSaveDialog(self):
    '''GUI for saving the dicom file(s).
    '''
    #for iv in self.imageViews:
      #fd = QtGui.QFileDialog(self)
      #fname = fd.getSaveFileName(self, "Save DICOM", iv.getFilename())
      #if len(fname) == 0:
        #continue
      #iv.saveView(fname)
    for iv in self.imageViews:
      iv.saveMetadata()

  def setBCSlider(self, iv):
    logger.debug('StartQT4::setBCSlider(%d)' % (iv.viewNum))
    (iMin, iMax) = iv.getImageMinMax()
    if iMax < 255:
      iMax = 255
    #view = iv.getViewShortName()
    if iv.viewNum == 1:
      self.ui.view1SliderMin.setMinimum(0)
      self.ui.view1SliderMin.setMaximum(iMax)
      self.ui.view1SliderMax.setMinimum(1)
      self.ui.view1SliderMax.setMaximum(iMax)
      self.ui.view1SliderMin.setProperty("value", iMin)
      self.ui.view1SliderMax.setProperty("value", iMax)
      self.ui.view1SliderMin.setValue(iMin)
      self.ui.view1SliderMax.setValue(iMax)
      self.ui.view1SliderMin.valueChanged.connect(partial(self.adjustViewBrightnessContrast, 1))
      self.ui.view1SliderMax.valueChanged.connect(partial(self.adjustViewBrightnessContrast, 1))
    if iv.viewNum == 2:
      self.ui.view2SliderMin.setMinimum(0)
      self.ui.view2SliderMin.setMaximum(iMax)
      self.ui.view2SliderMax.setMinimum(1)
      self.ui.view2SliderMax.setMaximum(iMax)
      self.ui.view2SliderMin.setProperty("value", iMin)
      self.ui.view2SliderMax.setProperty("value", iMax)
      self.ui.view2SliderMin.setValue(iMin)
      self.ui.view2SliderMax.setValue(iMax)
      self.ui.view2SliderMin.valueChanged.connect(partial(self.adjustViewBrightnessContrast, 2))
      self.ui.view2SliderMax.valueChanged.connect(partial(self.adjustViewBrightnessContrast, 2))

  def rotateData90(self, angle=None, view=None):
    '''rotate image data in multiples og 90 degrees
    '''
    count = 0
    if angle is None:
      count = 1
      direction = self.sender().text()
    else:
      if angle in (90, 180, 270):
        count = angle / 90
      direction = 'RR'
    while count > 0:
      if view is None:
        for iv in self.imageViews:
          iv.rotateData90(direction)
      else:
        view.rotateData90(direction)
      self.updateProgressLog('Rotate: '+direction)
      count -= 1
    self.emit(QtCore.SIGNAL("refreshDisplay"))

  def rotateUsingROI(self):
    for iv in self.imageViews:
      iv.showSummedImage(self.summedSens)
      iv.rotateByROI()
    self.currentOperation = 'ROTATE'
    self.setButtonsAndMenus('StartProcess')

  def setLateralAngle(self):
    default = -35.0
    angle, ok = QtGui.QInputDialog.getDouble(self, 'Rotate Lateral', 'Degrees', default)
    if ok:
      for iv in self.imageViews:
        if iv.getViewShortName() == 'LAT':
          iv.doRotateROI(False, angle)
          self.latAngle = abs(angle)
    self.emit(QtCore.SIGNAL("refreshDisplay"))

  #def doRotateROI(self, cancel=False):
    #for iv in self.imageViews:
      #a = iv.doRotateROI(cancel)
      #if iv.getViewShortName() == 'LAT':
        #self.latAngle = abs(a)
    #self.emit(QtCore.SIGNAL("refreshDisplay"))
    ##print(self.latAngle)

  def doRotateROI(self, cancel=False):
    for iv in self.imageViews:
      a = iv.doRotateROI(cancel)
      if iv.getViewShortName() == 'LAT':
        self.latAngle = abs(a)
    #for k, v in self.imageViewDict.items():
      #a = v['class'].doRotateROI(cancel)
      #if k == 'LAT':
        #self.latAngle = abs(a)
    self.emit(QtCore.SIGNAL("refreshDisplay"))
    #print(self.latAngle)

  def smoothData(self, view=None):
    '''Apply smoothing filter
    '''
    self.updateProgressLog('Smooth data')
    if view is None:
      for iv in self.imageViews:
        iv.smoothData()
    else:
      view.smoothData()
    self.emit(QtCore.SIGNAL("refreshDisplay"))

  def scaleData(self):
    '''Scale image data
    '''
    self.updateProgressLog('Scale data')
    for iv in self.imageViews:
      iv.scaleData()
    self.emit(QtCore.SIGNAL("refreshDisplay"))

  def setAnalysisLimits(self):
    '''Set limits for calculating centre of mass
    '''
    frameFrom = self.ui.spinFrom.value()
    frameTo = self.ui.spinTo.value()
    logger.debug('StartQT4::setAnalysisLimits() %d %d' % (frameFrom, frameTo))
    for iv in self.imageViews:
      iv.setAnalysisLimits(frameFrom, frameTo)
      
  def setVelocityLimits(self):
    '''Set range for calculating velocity
    '''
    default = 30
    mid, ok = QtGui.QInputDialog.getInt(self, 'Calculate velocity limits', 'Midpoint', default)
    if ok:
      for iv in self.imageViews:
        iv.calcVelocityLimits(mid)      
      
  def calculateVelocity(self):
    '''Calculate mucus velocity
    '''
    default = 30
    for iv in self.imageViews:
      angle = 0.0
      if iv.getViewShortName() == 'ANT':
        angle = self.latAngle
      vn = iv.getViewName()
      mid, ok = QtGui.QInputDialog.getInt(self, 'Calculate velocity limits', ' %s Midpoint' % vn, default)
      if ok:
        iv.calculateVelocity(mid, angle, self.conf['Tracking'])
    self.emit(QtCore.SIGNAL("refreshPlots"))

  def setTrackingThreshold(self):
    thr, ok = QtGui.QInputDialog.getDouble(self, 'Set Threshold', 'Threshold', 0.8)
    if ok:
      for iv in self.imageViews:
        iv.setTrackingThreshold(thr)      
    

  def changeTracking(self, update=None):
    '''Set the tracking method for centre of mass
    '''
    logger.debug('StartQT4::(changeTracking) %s' % (update))
    if update is not None:
      if self.conf['Tracking'] == 'No_ROI':
        self.ui.radioCOMFrame.setChecked(True)
      elif self.conf['Tracking'] == 'Fixed_ROI':
        self.ui.radioCOMInside.setChecked(True)
      elif self.conf['Tracking'] == 'Moving_ROI':
        self.ui.radioCOMPeak.setChecked(True)
    if self.ui.radioCOMFrame.isChecked():
      self.conf['Tracking'] = 'No_ROI'
      self.ui.actionTrackNoROI_Active.setChecked(True)
      self.ui.actionTrackFixedROI_Active.setChecked(False)
      self.ui.actionTrackMovingROI_Active.setChecked(False)
    if self.ui.radioCOMInside.isChecked():
      self.conf['Tracking'] = 'Fixed_ROI'
      self.ui.actionTrackNoROI_Active.setChecked(False)
      self.ui.actionTrackFixedROI_Active.setChecked(True)
      self.ui.actionTrackMovingROI_Active.setChecked(False)
    if self.ui.radioCOMPeak.isChecked():
      self.conf['Tracking'] = 'Moving_ROI'
      self.ui.actionTrackNoROI_Active.setChecked(False)
      self.ui.actionTrackFixedROI_Active.setChecked(False)
      self.ui.actionTrackMovingROI_Active.setChecked(True)
    self.removeCOMPlot()
    for iv in self.imageViews:
      iv.removeCOM()

  def resetCOMLimits(self, first=None, last=None):
    logger.debug('StartQT4::resetCOMLimits() %d' % (self.lastFrame))
    if first is None:
      first = self.firstFrame
    if last is None:
      last = self.lastFrame
    logger.debug('Range: %d - %d' % (first, last))
    self.ui.spinFrom.setMinimum(first)
    self.ui.spinTo.setMaximum(last)
    self.ui.spinFrom.setProperty("value", first)
    self.ui.spinTo.setProperty("value", last)

  def trackAuto(self):
    '''Find the centre of mass of each slice
    '''
    logger.debug('StartQT4::trackAuto()')
    for iv in self.imageViews:
      iv.invalidateOldCOM()
    if self.ui.actionTrackNoROI_Active.isChecked():
      self.conf['Tracking'] = 'No_ROI'
      self.trackNoROI()
    elif self.ui.actionTrackFixedROI_Active.isChecked():
      self.conf['Tracking'] = 'Fixed_ROI'
      self.trackFixedROI()
    elif self.ui.actionTrackMovingROI_Active.isChecked():
      self.conf['Tracking'] = 'Moving_ROI'
      self.trackMovingROI()
    self.emit(QtCore.SIGNAL("refreshDisplay"))
    self.setButtonsAndMenus('CalcCOM', self.conf['Tracking'])
    self.setViews(None)
    if self.lpl is not None:
      self.emit(QtCore.SIGNAL("refreshPlots"))
      
  def trackNoROI(self):
    logger.debug('StartQT4::trackNoROI()')
    self.updateProgressLog('Find Centre of Mass in frame')
    for iv in self.imageViews:
      iv.trackWithoutROI(self.measurementUnits)
      self.setShowOverlays()

  def trackFixedROI(self):
    logger.debug('StartQT4::trackFixedROI()')
    self.updateProgressLog('Find Centre of Mass in ROI')
    for iv in self.imageViews:
      iv.trackFixedROI()
      self.setShowOverlays()

  def trackMovingROI(self):
    logger.info('StartQT4::trackMovingROI()')
    self.updateProgressLog('Track peak Centre of Mass')
    for iv in self.imageViews:
      iv.trackMovingROI()
      self.setShowOverlays()

  def showROIPos(self):
    for iv in self.imageViews:
      iv.showROIPos()

  def plotResults(self):
    pass

  def plotCentreOfMass(self, coms=None):
    '''Plot horizontal and vertical movement
    '''
    logger.debug('StartQT4::plotCentreOfMass()')
    print(self.lpl)
    self.removeCOMPlot()
    if self.lpl is None:
      self.lpl = DualPlots(self.conf)
      self.comPlotFlag = True
      for iv in self.imageViews:
        iv.plotCentreOfMass(self.lpl)
      self.lpl.showPlotWin()

  def removeCOMPlot(self):
    logger.debug('StartQT4::removeCOMPlot()')
    if self.lpl is not None:
      print(self.lpl.win)
      for iv in self.imageViews:
        iv.plotCentreOfMass(self.lpl)
      self.lpl.closeWindow()
      #self.ui.buttonVHPlot.setChecked(False)
      del self.lpl
      self.lpl = None
      #self.comPlot = None
      self.comPlotFlag = False

  def removeCCOMPlot(self):
    logger.debug('StartQT4::removeCCOMPlot()')
    if self.mpl is not None:
      for iv in self.imageViews:
        iv.manualTrackingPlot(self.lpl)
      self.mpl.closeWindow()
      del self.mpl
      self.mpl = None

  def refreshPlots(self):
    logger.debug('StartQT4::refreshPlots()')
    if self.lpl is not None:
      for iv in self.imageViews:
        self.lpl.clearPlots(iv.getViewName())
      for iv in self.imageViews:
        iv.refreshPlots(self.lpl)
      #self.lpl.showPlotWin()   
    if self.mpl is not None:
      for iv in self.imageViews:
        self.mpl.clearPlots(iv.getViewName())
      for iv in self.imageViews:
        iv.refreshPlots(self.lpl)

  def printVirtical(self):
    '''Print virtical plot
    '''
    for iv in self.imageViews:
      iv.printVirtical()
    #if self.comPlotFlag == True:
      #self.vhpl.printVirtical()
    
  def printLateral(self):
    '''Print lateral plot
    '''
    for iv in self.imageViews:
      iv.printLateral()
    #if self.comPlotFlag == True:
      #self.vhpl.printLateral()
      
  def straighten(self):
    '''translate data to minimise horizontal drift
    '''
    for iv in self.imageViews:
      iv.straighten()
    #if self.comPlotFlag == True:
      #self.vhpl.fixVirtical()
  
  def exportPlotData(self):
    '''Save plot data in a csv file
    '''
    logger.debug('StartQT4::exportPlotData()')
    #rows = self.cAData.getCOM(scaled=True)
    np.set_printoptions(precision=3)
    fname = self.conf['dcmName'][:-3] + 'CSV'
    fd = QtGui.QFileDialog(self)
    fname = fd.getSaveFileName(self, "Save CSV", fname)
    if len(fname) == 0:
      return
    with open(fname, 'wb') as csvfile:
      for iv in self.imageViews:
        rows = iv.getExportData()
        logger.debug(len(rows))
        if rows is not None:
          dbswriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
          for row in rows:
            dbswriter.writerow(row)
    
  def toggleSummedImage(self):
    '''View frames as a single combined image
    '''
    if self.isSummedImage is True:
      self.isSummedImage = False
      self.emit(QtCore.SIGNAL("refreshDisplay"))
    else:
      for iv in self.imageViews:
        iv.showSummedImage(self.summedSens)
      self.isSummedImage = True
      self.updatePlot3d()
    
  def removeBackground(self, view=None):
    '''Remove counts below a threshold
    '''
    logger.debug('StartQT4::removeBackground()')
    if view is None:
      for iv in self.imageViews:
        iv.removeBackground()
    else:
      view.removeBackground()
    #if self.ui.buttonVHPlot.isChecked():
      #self.ui.buttonVHPlot.setChecked(False)
    self.updateProgressLog('Remove Background')
    self.emit(QtCore.SIGNAL("refreshDisplay"))
    
  def showPrevFrame(self):
    if self.imgIndex > 0:
      self.imgIndex -= 1
    self.ui.imageSlider.setValue(self.imgIndex)
    #self.emit(QtCore.SIGNAL("refreshDisplay"))
     
  def showNextFrame(self, loop=False):
    if self.imgIndex < self.lastFrame:
      self.imgIndex += 1
    elif loop == True:
      self.imgIndex = 0;
    self.ui.imageSlider.setValue(self.imgIndex)
    #self.emit(QtCore.SIGNAL("refreshDisplay"))

  def showFirstFrame(self):
    self.imgIndex = 0
    self.ui.imageSlider.setValue(self.imgIndex)

  def showLastFrame(self):
    self.imgIndex = self.lastFrame
    self.ui.imageSlider.setValue(self.imgIndex)

  def showFrame(self, value):
    self.imgIndex = value
    self.emit(QtCore.SIGNAL("refreshDisplay"))
     
  def refreshDisplay(self):
    logger.debug('StartQT4::refreshDisplay()')
    for iv in self.imageViews:
      iv.setimgIndex(self.imgIndex)
      iv.refreshDisplay(self.imgIndex)
    if self.is3dPloted:
        self.updatePlot3d()
    self.updateImageStatus()
    
  def togglePlot3d(self):
    logger.debug('StartQT4::togglePlot3d()')
    img = self.imageViews[0]
    if self.is3dPloted is False:
      #self.gpl = GlPlot(self.win3d, pType='render')
      self.gpl = GlPlot(pType='render')
      QtCore.QObject.connect(self.gpl.win, QtCore.SIGNAL('triggered()'), self.closeEvent)
      #self.connect(self.closeEvent, QtCore.SIGNAL('triggered()'), self.close3d)
      #self.connect(self.closeEvent, QtCore.SIGNAL('triggered()'))
      if self.isSummedImage is True:
        for iv in self.imageViews:
          self.gpl.initRenderPlot(iv.getViewSum(), iv.getViewName())
      else:
        for iv in self.imageViews:
          self.gpl.initRenderPlot(iv.getViewFrame(self.imgIndex), iv.getViewName())
      self.is3dPloted = True
      self.gpl.showWindow()
    else:
      self.gpl.closeWindow()
      self.gpl = None
      self.is3dPloted = False
      self.ui.buttonRender.setChecked(False)
    #self.gpl = GlPlot(pType='mesh')
    #self.gpl.initMeshPlot(self.dcmData[self.imgIndex])

  def close3d(self):
    print('3d closed')

  def set3dZScale(self):
    if self.gpl is not None:
      zsc, ok = QtGui.QInputDialog.getDouble(self, 'Set Z Scale 0.01-0.99', 'Z Scale', value=0.3, min=0.01, max=0.99, decimals=2)
      if ok:
        self.gpl.setZScale(zsc)
        self.gpl.updateRenderPlot()
        for iv in self.imageViews:
          self.gpl.initRenderPlot(iv.getViewFrame(self.imgIndex), iv.getViewName())        

  def updatePlot3d(self):
    if self.is3dPloted is True:
      #img = self.imageViews[0]
      for iv in self.imageViews:
        self.gpl.updatePlot(iv.getViewFrame(self.imgIndex), iv.getViewName())
    
  def showDicomInfo(self):
    d = []
    for iv in self.imageViews:
      d.append(iv.showDicomInfo())
    QtGui.QMessageBox.information(self, "DICOM Information", "<pre> %s </pre>" % '\n'.join(d))
    
  def showFile(self):
      #print "%s records inserted" % records
      rows = self.getData()
      self.ui.maxLeft.setText("%s" % self.lrMax[0])
      self.ui.maxRight.setText("%s" % self.lrMax[1])
      self.ui.numberOfRows.setText("%s" % len(rows))
      tablemodel = MyTableModel(rows, self)
      self.ui.infoTableView.setModel(tablemodel)

  def updateImageStatus(self):
    logger.debug('StartQT4::updateImageStatus()')
    #line = "{frame:d}, {max:f} ".format(frame=self.imgIndex, max=self.cAData.getImageFrameMax(self.imgIndex))
    line = "{frame:d} ".format(frame=self.imgIndex)
    self.ui.labelFrameNumber.setText(str(self.imgIndex))
    #self.statusRight.setText(line)
    
  def setShowOverlays(self):
    logger.debug('StartQT4::setShowOverlays()')
    if self.ui.buttonShowOverlays.isChecked():
      logger.debug('StartQT4::setShowOverlays Checked')
      for iv in self.imageViews:
        #iv.enableOverlay('COM')
        iv.enableOverlays()
        #iv.showOverlay('COM')
    else:
      logger.debug('StartQT4::setShowOverlays Unchecked')
      for iv in self.imageViews:
        #iv.disableOverlay('COM')
        iv.disableOverlays()
    #self.dispA.hideCom()

  def addMaskROI(self):
    logger.debug('StartQT4::addMaskROI()')
    self.currentOperation = 'MASK'
    self.setButtonsAndMenus('StartProcess') 
    for iv in self.imageViews:
      iv.addROI(self.currentOperation)
      #iv.addMaskROI()
    
  def maskFrames(self):
    logger.debug('StartQT4::maskFrames()')
    popup = DualSpin(self)
    popup.updateSpin(self.firstFrame, self.lastFrame)
    popup.exec_()
    frf, frt = popup.getValues()
    self.updateProgressLog('Mask region from frame %d to %d' % (frf, frt))
    for iv in self.imageViews:
      iv.applyMaskROI(frf, frt+1)
      iv.refreshDisplay()
      iv.removeROI('MASK')
      #iv.removeMaskROI()
    #print(frf, frt)

  def removeMaskROI(self):
    for iv in self.imageViews:
      iv.removeROI('MASK')
      #iv.removeMaskROI()

  def addTrackingROI(self):
    for iv in self.imageViews:
      iv.addROI('TRACK')
      #iv.addTrackingROI()

  def removeTrackingROI(self):
    for iv in self.imageViews:
      iv.removeROI('TRACK')
      #iv.removeTrackingROI()

  def animateStartStop(self):
    if self.isAnimated == False:
      self.isAnimated = True
      self.timer.timeout.connect(self.animateLoop)
      self.animateLoop()
    else:
      self.isAnimated = False
      
  def animateLoop(self):
    if self.isAnimated == True:
      self.showNextFrame(True)
      self.timer.start(self.conf['AnimSpeed'])
      
  def setAnimationDelay(self):
    logger.debug('StartQT4::setAnimationDelay()')
    if self.ui.actionSet_Animation_Speed.isChecked():
      self.enableItems(['animDelaySlider'])
      self.showElements(['animDelaySlider'])
      self.ui.animDelaySlider.setMinimum(10)
      self.ui.animDelaySlider.setMaximum(500)
      self.ui.animDelaySlider.valueChanged.connect(self.animationSliderChanged)
      self.ui.animDelaySlider.setValue(self.conf['AnimSpeed'])
    else:
      self.disableItems(['animDelaySlider'])
      self.hideElements(['animDelaySlider'])
    #default = self.conf['AnimSpeed']
    #mid, ok = QtGui.QInputDialog.getInt(self, 'Set animation speed', 'Delay in msec', default)
    #if ok:
      #self.conf['AnimSpeed'] = mid

  def setAnimationDelaySlider(self):
    self.enableItems(['animDelaySlider'])
    self.showElements(['animDelaySlider'])
    self.ui.animDelaySlider.setMinimum(10)
    self.ui.animDelaySlider.setMaximum(500)
    self.ui.animDelaySlider.valueChanged.connect(self.animationSliderChanged)
    self.ui.animDelaySlider.setValue(self.conf['AnimSpeed'])

  def animationSliderChanged(self, value):
    self.conf['AnimSpeed'] = self.ui.animDelaySlider.value()

  def analyseCalibrationImage(self):
    self.currentOperation = 'CALIB'
    for iv in self.imageViews:
      iv.addROI(self.currentOperation)
      #iv.addCalibrationROIs()
    self.setButtonsAndMenus('StartProcess')

  def measurePixelSize(self):
    self.imageViews[-1].measurePixelSize()
    self.removeCalibrationROIs()

  def removeCalibrationROIs(self):
    self.imageViews[-1].removeCalibrationROIs()

  def setSummedSensitivity(self):
    default = 2
    sens, ok = QtGui.QInputDialog.getInt(self, 'Set sensitivity factor for Summed Image', 'Range 0-9', default, min=0, max=9)
    if ok:
      self.summedSens = sens

  def doProcessProceed(self):
    logger.debug('StartQT4::doProcessProceed()')
    if self.currentOperation is None:
      return
    if self.currentOperation == 'ROTATE':
      self.doRotateROI()
    if self.currentOperation == 'INSIDE':
      self.doMeasureSizeInsideROI()
    if self.currentOperation == 'MASK':
      self.maskFrames()
    if self.currentOperation == 'CALIB':
      self.measurePixelSize()
    self.setButtonsAndMenus('StopProcess')

  def doProcessCancel(self):
    logger.debug('StartQT4::doProcessProceed()')
    if self.currentOperation == 'ROTATE':
      self.doRotateROI(True)
    if self.currentOperation == 'INSIDE':
      self.doMeasureSizeInsideROI(False)
    if self.currentOperation == 'MASK':
      self.removeMaskROI()
    if self.currentOperation == 'CALIB':
      self.removeCalibrationROIs()
    self.setButtonsAndMenus('StopProcess')
    self.currentOperation = None

  def measureSizeInsideROI(self):
    self.currentOperation = 'INSIDE'
    self.setButtonsAndMenus('StartProcess') 
    for iv in self.imageViews:
      iv.showSummedImage(self.summedSens)
      iv.addROI(self.currentOperation)
      #iv.measureSizeInsideROI()

  def doMeasureSizeInsideROI(self, measure=True):
    for iv in self.imageViews:
      iv.doMeasureSizeInsideROI(measure)
    self.emit(QtCore.SIGNAL("refreshDisplay"))

  def setPixelSize(self):
    psize, ok = QtGui.QInputDialog.getDouble(self, 'Set Pixel Size', 'Size', 3.3)
    if ok:
      for iv in self.imageViews:
        iv.overridePixelSize(psize)
      self.overridePixelFlag = True
      self.overridePixelSize = psize

  def setBCAuto(self, vn):
    logger.debug('StartQT4::setBCAuto(%d)' % vn)
    if vn == 1:
      if self.ui.view1BCAutoCheckbox.isChecked():
        fmin = None
        fmax = None
      else:
        fmin = self.ui.view1SliderMin.value()
        fmax = self.ui.view1SliderMax.value()
    if vn == 2:
      if self.ui.view2BCAutoCheckbox.isChecked():
        fmin = None
        fmax = None
      else:
        fmin = self.ui.view2SliderMin.value()
        fmax = self.ui.view2SliderMax.value()
    for iv in self.imageViews:
      if iv.viewNum == vn:
        iv.setBrightnessContrast(fmin, fmax)
    self.emit(QtCore.SIGNAL("refreshDisplay"))
    
  def adjustViewBrightnessContrast(self, vn, value):
    logger.debug('StartQT4::adjustViewBrightnessContrast(%d, %s)' % (value, vn))
    # this callback is incorrectly triggered on file load
    if self.loadingFlag:
      return
    if vn == 1:
      self.ui.view1BCAutoCheckbox.setChecked(False)
      fmin = self.ui.view1SliderMin.value()
      fmax = self.ui.view1SliderMax.value()
    if vn == 2:
      self.ui.view2BCAutoCheckbox.setChecked(False)
      fmin = self.ui.view2SliderMin.value()
      fmax = self.ui.view2SliderMax.value()
    for iv in self.imageViews:
      if iv.viewNum == vn:
        iv.setBrightnessContrast(fmin, fmax)
    self.emit(QtCore.SIGNAL("refreshDisplay"))

  def addIsocurveROI(self):
    logger.info('StartQT4::addIsocurveROI()')
    self.currentOperation = 'ISO'
    self.ui.view1SliderMin.setMaximum(50)
    self.ui.view2SliderMin.setMaximum(50)
    self.ui.view1SliderMin.valueChanged.disconnect()
    self.ui.view2SliderMin.valueChanged.disconnect()
    self.ui.view1SliderMin.valueChanged.connect(self.updateIsocurveROI)
    self.ui.view2SliderMin.valueChanged.connect(self.updateIsocurveROI)
    for iv in self.imageViews:
      iv.addIsocurveROI(0, 0)

  def removeIsocurveROI(self):
    logger.debug('StartQT4::removeIsocurveROI()')
    self.ui.view1SliderMin.valueChanged.disconnect()
    self.ui.view2SliderMin.valueChanged.disconnect()
    for iv in self.imageViews:
      self.setBCSlider(iv)
    #for k in self.imageViewDict.keys():
      #(iMin, iMax) = self.imageViewDict[k]['class'].getImageMinMax()
      #self.setBCSlider(k, iMin, iMax)

  def updateIsocurveROI(self):
    logger.info('StartQT4::updateIsocurveROI()')
    ca = self.ui.view1SliderMin.value()
    cl = self.ui.view2SliderMin.value()
    for iv in self.imageViews:
      iv.addIsocurveROI(ca, cl)

  def showIsocurveValues(self):
    for iv in self.imageViews:
      iv.showIsocurveValues()
    
  def isocurveThreshold(self):
    for iv in self.imageViews:
      iv.isocurveThreshold()
    self.removeIsocurveROI()

  def setManualType(self, t):
    self.trackManualType = t
    if t == 'Movement':
      self.ui.actionManual_COM.setChecked(True)
      self.ui.actionManual_Spiral.setChecked(False)
    if t == 'Spiral':
      self.ui.actionManual_COM.setChecked(False)
      self.ui.actionManual_Spiral.setChecked(True)

  def trackingStart(self, ttype):
    logger.debug('StartQT4::trackingStart(%s)' % ttype)
    self.trackingStop()
    self.trackManualType = ttype
    menuTrack = 'actionTrack' + ttype + '_Active'
    menuView = 'actionView_' + ttype
    getattr(self.ui, menuTrack).setChecked(True)
    getattr(self.ui, menuView).setChecked(True)
    self.enableItems([menuView])
    self.trackManualFlag = True
    for iv in self.imageViews:
      iv.setTrackMouse(self.trackManualFlag, self.trackManualType)
    QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

  def trackingStop(self):
    logger.debug('StartQT4::trackManualStop()')
    for t in ('Movement', 'Spiral'):
      if self.trackManualFlag == True and t == self.trackManualType:
        self.trackManualFlag = False
        for iv in self.imageViews:
          iv.setTrackMouse(self.trackManualFlag, self.trackManualType)
        QtGui.QApplication.restoreOverrideCursor()

  def setTrackingViewStatus(self, ttypes):
    for t in ttypes:
      menuView = 'actionView_' + t
      getattr(self.ui, menuView).setChecked(True)
      self.enableItems([menuView])

  def trackManualStart(self):
    logger.debug('StartQT4::trackManualStart()')
    self.trackManualFlag = True
    for iv in self.imageViews:
      iv.setTrackMouse(self.trackManualFlag, self.trackManualType)
    QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

  def trackManualStop(self):
    logger.debug('StartQT4::trackManualStop()')
    self.trackManualFlag = False
    for iv in self.imageViews:
      iv.setTrackMouse(self.trackManualFlag, self.trackManualType)
    QtGui.QApplication.restoreOverrideCursor()

  def trackManualPlot(self):
    logger.debug('StartQT4::trackManualPlot()')
    #mplot = ManualPlot()
    for iv in self.imageViews:
      iv.makeTrackingPlots()
    #if self.mpl is None:
      #self.mpl = XYPlots()
      #for iv in self.imageViews:
        #iv.manualTrackingPlot(self.mpl)
      #self.mpl.showPlotWin()
      #self.setButtonsAndMenus('CalcCOM')
    else:
      self.removeCCOMPlot()

  def removeCCOMPlot(self):
    logger.debug('StartQT4::removeCCOMPlot()')
    if self.mpl is not None:
      for iv in self.imageViews:
        iv.manualTrackingPlot(self.mpl)
      self.mpl.closeWindow()
      del self.mpl
      self.mpl = None

  def removePlots(self):
    logger.debug('StartQT4::removePlots()')
    for iv in self.imageViews:
      iv.removePlots()

  def trackManualClear(self):
    for iv in self.imageViews:
      iv.trackManualClear()

  def trackManualCalcVelocity(self):
    for iv in self.imageViews:
      iv.trackManualCalcVelocity(self.latAngle)

  def trackView(self, ttype):
    logger.debug('StartQT4::trackView(%s)' % ttype)
    menuView = 'actionView_' + ttype
    if getattr(self.ui, menuView).isChecked():
      for iv in self.imageViews:
        iv.enableOverlay(ttype)
    else:
      for iv in self.imageViews:
        iv.disableOverlay(ttype)

  def setViews(self, vlist):
    logger.debug('StartQT4::setViews()')
    if vlist is None:
      vlist = []
      for iv in self.imageViews:
        vlist += iv.getActiveTracking()
    for v in vlist:
      menuView = 'actionView_' + v
      getattr(self.ui, menuView).setChecked(True)
      self.enableItems([menuView])


class DualSpin(QtGui.QDialog, Ui_DualSpin):  
  def __init__(self, parent = None):
    QtGui.QWidget.__init__(self, parent)
    self.frameFrom = 0
    self.frameTo = 0
    self.status = 0
    self.setupUi(self)

  def updateSpin(self, ff, lf):
    self.spinFrom.setProperty("value", ff)
    self.spinTo.setProperty("value", lf)
    
  def closeEvent(self, event):
    self.deleteLater()
    event.accept()

  def acceptEvent(self, event):
    self.deleteLater()
    event.accept()
    
  def getValues(self):
    if self.status:
      return self.frameFrom, self.frameTo
    else:
      return 0, 0

  def accept(self):
    self.frameFrom = self.spinFrom.value()
    self.frameTo = self.spinTo.value()
    self.status = 1
    self.close()

  def reject(self):
    self.status = 0
    self.close()
  




class Obj(QtGui.QGraphicsObject):
    def __init__(self):
        QtGui.QGraphicsObject.__init__(self)
        pg.GraphicsScene.registerObject(self)
        
    def paint(self, p, *args):
      pass
        #p.setPen(pg.mkPen(200,200,200))
        #p.drawRect(self.boundingRect())
        
    def boundingRect(self):
        return QtCore.QRectF(0, 0, 20, 20)
        
    #def mouseClickEvent(self, ev):
        #if ev.double():
            #print("double click")
        #else:
            #print("click")
        #ev.accept()
        
    def HoverEvent(self):
      logger.info('H')
      logger.info(ev.pos())


class ImageDisplayTest(QtGui.QGraphicsObject):
  def __init__(self, ui, view, parent=None):
    logger.debug('  ImageDisplayTest::__init__(%s)' % view)
    pg.mkQApp()
    self.COMData = None
    self.CCOMData = None
    self.vb = pg.ViewBox(enableMenu=False)
    self.vb.setAspectLocked()
    self.img = pg.ImageItem()
    self.vb.addItem(self.img)
    self.sp = pg.ScatterPlotItem()
    self.addDisplayItem('SPLOT', self.sp)


def readTag(config, section, tagtype, tag, defaultValue):
  try:
    val = config.get(section, tag)
  except:
    val = defaultValue
  if tagtype == 'bool':
    if val == 'True':
      val = True
    else:
      val = False
  if tagtype == 'int':
    val = int(val)
  return val

class DefaultValue(UserDict):
  "store ini file values"
  def __init__(self, filename=None):
    UserDict.__init__(self)
    self["iniName"] = filename

class LoadDefaults(DefaultValue):
  iniTags = {"Units"    : ('Defaults', 'text', 'fr'),
      "Tracking"     : ('Defaults', 'text', 'NO_ROI'),
      "DataDir"      : ('Defaults', 'text', '.'),
      "AnimSpeed"     : ('Defaults', 'int', '100'),
      "debuglevel"    : ('Defaults', 'text', 'ERROR'),
      "ResultsDir"    : ('Defaults', 'text', '/tmp'),
      "HidePatientID"    : ('Defaults', 'bool', 'False'),
      "Rotate"      : ('Image Load', 'int', '90'),
      "Smooth"      : ('Image Load', 'bool', 'True'),
      "RemoveBackground"  : ('Image Load', 'bool', 'True'),
      "PlotSize"    : ('Plots', 'text', '800x600'),
      "ShowXFit"    : ('Plots', 'bool', 'True'),
      "XPlotTitle"  : ('Plots', 'text', "X movement"),
      "YPlotTitle"  : ('Plots', 'text', "Y movement"),
      "LeftPlotTitle"   : ('Plots', 'text', "Default"),
      "RightPlotTitle"  : ('Plots', 'text', "Default"),
      "ShowTitle"   : ('Plots', 'bool', "True")
      }

  def __parse(self, filename):
    "parse ID3v1.0 tags from MP3 file"
    self.clear()
    try:
      config = ConfigParser.ConfigParser()
      config.read((filename))
      #ds = dicom.read_file(filename)
      for tag, (section, tagtype, defVal) in self.iniTags.items():
        self[tag] = readTag(config, section, tagtype, tag, defVal)               
    except IOError:
      print("Error opening %s" % filename)
      pass

  def __setitem__(self, key, item):
      if key == "iniName" and item:
        self.__parse(item)
      DefaultValue.__setitem__(self, key, item)



#class Initialization:
  #def __init__(self):
    #config = ConfigParser.ConfigParser()
    #config.read(('ciliac.cfg', 'config\ciliac.cfg'))
      ##logger.error('Could not load configuration file')
      ##sys.exit(1)
    #logger.info('Load defaults from ciliac.cfg')
    #self.defaults = {}
    #self.imgLoad = {}
    #self.defaults['units'] = config.get('Defaults', 'Units')
    #if self.defaults['units'] == 'frame':
      #self.defaults['units'] = 'fr'
    #self.defaults['tracking'] = config.get('Defaults', 'Tracking')
    #self.defaults['datadir'] = config.get('Defaults', 'DataDir')
    #self.defaults['animspeed'] = config.get('Defaults', 'AnimSpeed')
    #self.defaults['debuglevel'] = config.get('Defaults', 'debuglevel')
    #self.defaults['resultsdir'] = config.get('Defaults', 'ResultsDir')
    #self.imgLoad['rotate'] = int(config.get('Image Load', 'Rotate'))
    #self.imgLoad['smooth'] = False
    #self.defaults['hidepatientid'] = False
    #if config.get('Defaults', 'HidePatientID') == 'True':
      #self.defaults['hidepatientid'] = True
    #if config.get('Image Load', 'Smooth') == 'True':
      #self.imgLoad['smooth'] = True
    #self.imgLoad['removebackground'] = False
    #if config.get('Image Load', 'RemoveBackground') == 'True':
      #self.imgLoad['removebackground'] = True
    
  #def __setitem__(self, i, x):
    #pass
  
  #def getDefaults(self, val):
    #return self.defaults[val]
  
  #def getImgDefault(self, val):
    #return self.imgLoad[val]
  

def main():
  app = QtGui.QApplication(sys.argv)
  ex = StartQT4()
  ex.show()
  app.processEvents()  ## force complete redraw for every plot
  sys.exit(app.exec_())

    
if __name__ == '__main__':
    main()
    pass
  