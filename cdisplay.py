from PyQt4 import QtCore, QtGui
from debugging import *
import pyqtgraph as pg
import numpy as np

class ImageDisplay(QtGui.QGraphicsObject):
  def __init__(self, ui, view, parent=None):
    logger.debug('  ImageDisplay::__init__(%s)' % view)
    pg.mkQApp()
    self.COMData = None
    self.CCOMData = None
    self.cData = None
    self.imgData = None
    self.isocurve = 0
    self.overlays = {}
    self.vblist = []
    self.itemList = {
      'COM':[None, True], 
      'Movement':[None, True], 
      'Spiral':[None, True], 
      'spots':[None, True], 
      'TRACK':[None, True], 
      'MASK':[None, True], 
      'CALIBA':[None, True], 
      'CALIBB':[None, True], 
      'ROTATE':[None, True], 
      'INSIDE':[None, True],
      'ISOCURVE':[None, True],
      'SPLOT':[None, False]
      }
    self.overlayDict = dict(COM=None, TRACK=None, MASK=None, CALIBA=None, CALIBB=None, ROTATE=None, SIZE=None)
    self.vb = pg.ViewBox(enableMenu=False)
    self.vb.setAspectLocked()
    self.img = pg.ImageItem()
    #self.img = pg.ImageView()
    self.rotImg = None
    self.rotROI = None
    #self.addDisplayItem('IMG', self.img)
    self.vb.addItem(self.img)
    self.sp = pg.ScatterPlotItem()
    self.addDisplayItem('SPLOT', self.sp)
    self.hist = None
    if view != "Dummy":
      getattr(ui, view).setCentralItem(self.vb)
      #getattr(ui, view).setCentralItem(self.img)
    self.isRendered = False
    self.enabledOverlays = {}
    self.validOverlays = {}
    self.showCOMOverlay = False
    self.mousePos = (0, 0)
    self.saveMouseFlag = False
    #self.maskROI = None
    #self.trackingROI = None
    #self.calibROIa = None
    #self.calibROIb = None
    #print (self.vb.allChildren())
    #pl = self.ui.graphicsView.addPlot()
    #proxy = pg.SignalProxy(pl.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
    if view != "Dummy":
      self.vb.scene().sigMouseMoved.connect(self.mouseMoved)

  def setMouseFlag(self, f):
    self.saveMouseFlag = f

  def addDisplayItem(self, itemType, item):
    logger.debug('  ImageDisplay::addDisplayItem(%s)' % (itemType))
    if itemType == 'COM':
      self.sp.setData(x=[self.COMData[0]],y=[self.COMData[1]], symbol='+', size=15, pen=('y'))
    elif itemType == 'Movement':
      self.sp.setData(x=[item[0]],y=[item[1]], symbol='+', size=15, pen=('r'))
      #self.sp.setData(spots)
      item = None
    elif itemType == 'Spiral':
      self.sp.setData(x=[item[0]],y=[item[1]], symbol='+', size=15, pen=('c'))
      item = None
    elif itemType == 'spots':
      self.sp.setData(item)
      item = None
    else:
      self.vb.addItem(item)
    #self.itemList[itemType][0] = item
    #self.overlays[itemType] = (item, True)

  #def showDisplayItems(self, itemType):
    #logger.debug('  ImageDisplay::showDisplayItem(%s)' % itemType)
    #if itemType == 'COM' and self.itemList[itemType][0] is not None:
      #self.sp.setData(x=[self.COMData[0]],y=[self.COMData[1]], symbol='+', size=15, pen=('y'))
    #elif itemType == 'Movement' and self.itemList[itemType][0] is not None:
      #self.sp.setData(x=[self.mousePos[0]],y=[self.mousePos[1]], symbol='+', size=15, pen=('r'))
    #elif itemType == 'Spiral' and self.itemList[itemType][0] is not None:
      #self.sp.setData(x=[self.mousePos[0]],y=[self.mousePos[1]], symbol='+', size=15, pen=('c'))
    #else:
      #if self.itemList[itemType][0] is not None:
        #self.vb.addItem(self.itemList[itemType][0])

  def hideDisplayItem(self, itemType, item):
    logger.debug('  ImageDisplay::hideDisplayItem(%s)' % itemType)
    return
    if itemType in self.itemList:
      if itemType == 'COM':
        self.sp.clear()
      else:
        if self.itemList[itemType][1]:
          self.vb.removeItem(item)

  def removeDisplayItem(self, itemType, item):
    logger.debug('  ImageDisplay::removeDisplayItem(%s)' % itemType)
    if itemType in self.itemList:
      if itemType.find('COM') != -1:
        self.sp.clear()
      else:
        self.vb.removeItem(item)
      self.itemList[itemType][0] = None
      #self.itemList[itemType][1] = False

  def deleteAll(self):
    logger.debug('  ImageDisplay::deleteAll()')
    self.setDisplayImage(np.zeros((384, 384)))
    if self.COMData is not None:
      del self.COMData
      self.COMData = None
    self.disableOverlays()
    for item in self.itemList.keys():
      self.itemList[item][0] = None
      
  def setcData(self, cd):
    self.cData = cd

  def mouseMoved(self, pos):
    logger.debug('  ImageDisplay::mouseMoved() %s ' % self.img.mapFromScene(pos))
    xy = self.img.mapFromScene(pos)
    if self.saveMouseFlag:
      self.mousePos = (xy.x(), xy.y())

  def getMousePos(self):
    logger.debug('  ImageDisplay::getMousePos()')
    p = self.mousePos
    self.mousePos = (0, 0)
    return p

  def addMTROI(self, rData, roi=None):
    logger.debug('  ImageDisplay::addMTROI()')
    if roi is None:
      roi = pg.RectROI(rData.startPos, rData.startSize, pen=rData.pen)
    self.vblist.append(roi)
    rData.updateROI(roi)
    self.addDisplayItem(rData.roiType, roi)

  #def removeROI(self, roiType):
    #if self.itemList[roiType][0] is not None:
      #self.removeDisplayItem(roiType, self.itemList[roiType][0])

  def removeROI(self, roi=None):
    logger.debug('  ImageDisplay::removeROI()')
    #print(len(self.vblist))
    for i in self.vblist:
      self.vb.removeItem(i)
    self.vblist = []
    #if roi is not None:
      #self.vb.removeItem(roi)

  def moveTrackingROI(self, rData, imgIndex):
    logger.debug('  ImageDisplay::moveTrackingROI(%d)' % imgIndex)
    roi = rData.getROIScreenFrame(imgIndex)
    if roi is None:
      return
    self.removeROI(rData.roi)
    roi = pg.RectROI( [roi[0], roi[2]], [(roi[1]-roi[0]), (roi[3]-roi[2])], pen=rData.pen)
    self.addMTROI(rData, roi)

  def setDisplayImage(self, imgData, fmin=None, fmax=None):
    logger.debug('  ImageDisplay::setDisplayImage(%s)' % type(imgData))
    if imgData is None:
      return
    #print(imgData.max())
    self.sp.clear()
    #self.removeROI()
    #for c in clist:
      #print(c)
    if fmin is None:
      fmin = imgData.min()
    if fmax is None:
      fmax = imgData.max()
    #print(fmin, fmax)
    self.img.setImage(imgData, levels=(fmin, fmax))
    self.imgData = imgData
    if self.isocurve > 0:
      self.removeIsocurveROI()
      self.addIsocurveROI(self.isocurve)
    
  def getPixelSize(self):
    return self.img.pixelSize()
    #print(self.img.pixelSize())
  
  def showSpots(self, s):
    logger.debug('  ImageDisplay::showSpots')
    self.addDisplayItem('spots', s)

  #def addManualTrackPoint(self, t, f, x, y):
    #logger.debug('  ImageDisplay::addManualTrackPoint(%s)' % (t))
    #if t == 'Movement':
      #self.addDisplayItem('Movement', (x, y))
    #if t == 'Spiral':
      #self.addDisplayItem('Spiral', (x, y))
   
  #def addTrackingPoint(self, track, frame):
    #logger.info('  ImageDisplay::addTrackingPoint(%s)' % (frame))
    #tp = track.getManualTrackPoint(frame)
    #if tp is not None:
      #print ('Add %s: %d-%d, %s, %s' % (track.trackType, tp[1], tp[2], track.symbol, track.symbolColour))
      #self.sp.setData(x=[tp[1]],y=[tp[2]], symbol=track.symbol, size=track.symbolSize, pen=(track.symbolColour))
      #self.sp.setData(x=[tp[1]+2],y=[tp[2]+2], symbol=track.symbol, size=track.symbolSize, pen=('r'))
      #if track.trackType == 'Movement':
        #self.addDisplayItem('Movement', (tp[1], tp[2]))
      #if track.trackType == 'Spiral':
        #self.addDisplayItem('Spiral', (tp[1], tp[2]))
      
  #def getROIPos(self, roiType):
    #logger.debug('  ImageDisplay::getROIPos(%s)' % roiType)
    #if self.itemList[roiType][0] is None:
      #return None
    #pos = self.itemList[roiType][0].pos()
    ##print(pos)
    #w, h = self.itemList[roiType][0].size()
    #return (int(pos[0]), int(pos[0])+w, int(pos[1]), int(pos[1])+h)

  #def addMaskROI(self):
    #logger.debug('  ImageDisplay::addMaskROI()')
    #roi = pg.RectROI([50, 50], [20, 20], pen=(0,9))
    #self.addDisplayItem('MASK', roi)
    #return roi

  #def removeMaskROI(self):
    #self.removeDisplayItem('MASK', self.itemList['MASK'][0])

  #def showMaskROI(self, imgData):
    #pos = self.itemList['MASK'][0].pos()
    #w, h = self.itemList['MASK'][0].size()
    ##print(pos, w, h)

  #def getMaskROI(self):
    #pos = self.itemList['MASK'][0].pos()
    #w, h = self.itemList['MASK'][0].size()
    #return (int(pos[0]), int(pos[0])+w, int(pos[1]), int(pos[1])+h)

  #def addTrackingROI(self):
    #logger.debug('  ImageDisplay::addTrackingROI()')
    #roi = pg.RectROI([50, 50], [20, 20], pen=(3,9))
    #self.addDisplayItem('TRACK', roi)

  #def removeTrackingROI(self):
    #logger.debug('  ImageDisplay::removeTrackingROI()')
    #self.removeDisplayItem('TRACK', self.itemList['TRACK'][0])

  #def getTrackingROI(self):
    #logger.debug('  ImageDisplay::getTrackingROI()')
    #if self.itemList['TRACK'][0] is None:
      #return None
    #pos = self.itemList['TRACK'][0].pos()
    ##print(pos)
    #w, h = self.itemList['TRACK'][0].size()
    #return (int(pos[0]), int(pos[0])+w, int(pos[1]), int(pos[1])+h)
    ##return pos, w, h

  #def moveTrackingROI(self, roi):
    #logger.debug('  ImageDisplay::moveTrackingROI(%s)' % roi)
    #if roi is None or self.itemList['TRACK'][0] is None:
      #return
    #self.removeDisplayItem('TRACK', self.itemList['TRACK'][0])
    #roi = pg.RectROI([roi[0], roi[2]], [(roi[1]-roi[0]), (roi[3]-roi[2])], pen=(3,9))
    ##print([roi[0], roi[2]], [(roi[1]-roi[0]), (roi[3]-roi[2])])
    #self.addDisplayItem('TRACK', roi)

  #def getROIPosition(self, roi):
    #logger.debug('  ImageDisplay::()')
    #if self.itemList[roi][0] is None:
      #return None
    #pos = self.itemList[roi][0].pos()
    #w, h = self.itemList[roi][0].size()
    #return (pos, w, h)

  def addIsocurveROI(self, l):
    logger.debug('  ImageDisplay::addIsocurveROI(%s)' % l)
    self.isocurve = l
    if self.itemList['ISOCURVE'][0] is not None:
      self.removeIsocurveROI()
    roi = pg.IsocurveItem(data=self.imgData, level = l, pen = (3,9))
    roi.setZValue(10)
    self.addDisplayItem('ISOCURVE', roi)

  def removeIsocurveROI(self):
    logger.debug('  ImageDisplay::removeIsocurveROI()')
    self.removeDisplayItem('ISOCURVE', self.itemList['ISOCURVE'][0])

  def resetIsocurve(self):
    self.isocurve = 0

  def addCalibrationROIs(self):
    logger.debug('  ImageDisplay::addCalibrationROIs()')
    roia = pg.RectROI([30, 50], [10, 10], pen=(3,9))
    roib = pg.RectROI([60, 50], [10, 10], pen=(3,9))
    self.addDisplayItem('CALIBA', roia)
    self.addDisplayItem('CALIBB', roib)

  def getCalibrationROIs(self):
    pos = self.itemList['CALIBA'][0].pos()
    w, h = self.itemList['CALIBA'][0].size()
    a = (int(pos[0]), int(pos[0])+w, int(pos[1]), int(pos[1])+h)
    pos = self.itemList['CALIBB'][0].pos()
    w, h = self.itemList['CALIBB'][0].size()
    b = (int(pos[0]), int(pos[0])+w, int(pos[1]), int(pos[1])+h)
    return (a, b)

  def removeCalibrationROIs(self):
    logger.debug('  ImageDisplay::removeCalibrationROIs()')
    self.removeDisplayItem('CALIBA', self.itemList['CALIBA'][0])
    self.removeDisplayItem('CALIBB', self.itemList['CALIBB'][0])
      
  def showCalibCOM(self, posa, posb):
    self.sp.setData(pos=[posa, posb], symbol='+', size=20, pen=('y'))
    #self.sp.setData([posb[0]], y = [posb[1]], symbol='+', size=20)

  def addRotateROI(self, iMin, iMax):
    logger.debug('  ImageDisplay::addRotateROI()')
    #self.addValidOverlay('ROTATE')
    self.rotROI = pg.RectROI([0, 0], [64, 64], pen=(3,3))
    self.rotROI.addRotateHandle([0,1], [0.5, 0.5])
    self.addDisplayItem('ROTATE', self.rotROI)
    if iMin is not None:
      self.rotImg = pg.ImageItem(self.imgData, levels=(iMin, iMax))
    else:
      self.rotImg = pg.ImageItem(self.imgData)
    self.rotImg.setParentItem(self.rotROI)

  def getRotateROI(self):
    logger.debug('  ImageDisplay::getRotateROI()')
    if self.rotROI is None:
      return None
    #pos = self.overlayDict['ROTATE'].pos()
    #w, h = self.overlayDict['ROTATE'].size()
    a = self.rotROI.angle()
    return a
    #return pos, w, h

  def removeRotateROI(self):
    logger.debug('  ImageDisplay::removeRotateROI()')
    self.rotImg = None
    self.removeDisplayItem('ROTATE', self.rotROI)
    #self.itemlist['ROTATE'][0] = None
    self.rotROI = None

  #def addSizeROI(self):
    #logger.debug('  ImageDisplay::addSizeROI()')
    #roi = pg.RectROI([50, 50], [10, 20], pen=(3,6))
    #self.addDisplayItem('INSIDE', roi)

  #def getSizeROI(self):
    #logger.debug('  ImageDisplay::getSizeROI()')
    #if self.itemList['INSIDE'][0] is None:
      #return None
    #pos = self.itemList['INSIDE'][0].pos()
    #w, h = self.itemList['INSIDE'][0].size()
    ##print(w, h)
    #return w, h

  #def removeSizeROI(self):
    #logger.debug('  ImageDisplay::removeSizeROI()')
    #self.removeDisplayItem('INSIDE', self.itemList['INSIDE'][0])
    #self.itemList['INSIDE'][0] = None

  def enableOverlay(self, overlay):
    logger.debug('  ImageDisplay::enableOverlay(%s)' % overlay)
    self.enabledOverlays[overlay] = 1

  #def enableOverlays(self):
    #logger.debug('  ImageDisplay::enableOverlays()')
    #for k in self.overlayDict.keys():
      #self.showDisplayItems(k)
   

  def showOverlay(self, overlay):
    logger.debug('  ImageDisplay::showOverlay(%s)' % overlay)
    if self.isValidOverlay(overlay) is True:
      self.addDisplayItem('COM', None)
      #if overlay == 'COM':
        #self.sp.setData(x=[self.COMData[0]],y=[self.COMData[1]], symbol='+', size=15, pen=('y'))

  def disableOverlay(self, overlay):
    logger.debug('  ImageDisplay::disableOverlay(%s)' % overlay)
    if self.isValidOverlay(overlay) is True:
      if overlay == 'COM':
        #self.vb.removeItem(self.sp)
        self.sp.clear()
      #self.removeValidOverlay(overlay)
    if overlay in self.enabledOverlays:
      self.enabledOverlays.pop(overlay)

  def disableOverlays(self):
    logger.debug('  ImageDisplay::disableOverlays()')
    dlist = []
    for k in self.itemList.keys():
      if self.itemList[k][0] is not None:
        self.hideDisplayItem(k, self.itemList[k][0])
    
  def isEnabledOverlay(self, overlay):
    if overlay in self.enabledOverlays:
      return True
    else:
      return False
    
  def addValidOverlay(self, overlay):
    logger.debug('  ImageDisplay::addValidOverlay(%s)' % overlay)
    #print('addValidOverlay() '+overlay)
    self.validOverlays[overlay] = 1    
    
  def removeValidOverlay(self, overlay):
    logger.debug('  ImageDisplay::removeValidOverlay(%s)' % overlay)
    #print('removeValidOverlay() '+overlay)
    if overlay in self.validOverlays:
      if overlay == 'COM':
        #self.vb.removeItem(self.sp)
        self.sp.clear()
      self.validOverlays.pop(overlay)
    
  def isValidOverlay(self, overlay):
    if overlay in self.validOverlays:
      return True
    else:
      return False
    
  def hideCom(self):
    logger.debug('  ImageDisplay::hideCom()')
    #return
    self.hideDisplayItem('COM', 1)
    if self.isValidOverlay('COM') is True:
      self.sp.clear()
      self.removeValidOverlay('COM')
    
  def showCCOM(self, t, mtp):
    logger.debug('  ImageDisplay::showCCOM(%s %s)' % (t, mtp))
    if t == 'Movement':
      self.addDisplayItem('Movement', (mtp[1], mtp[2]))
    if t == 'Spiral':
      self.addDisplayItem('Spiral', (mtp[1], mtp[2]))

  #def redrawDisplay(self):
    #if self.imgData == None:
      #return
    #for overlay in self.enabledOverlays:
      #redrawOverlay

  #def showCOM(self, com, enabled):
    #logger.debug('  ImageDisplay::showCOM(%d)' % enabled)
    #if com is None:
      #logger.debug('com is None')
      ##self.hideCom()
      #self.removeDisplayItem('COM', 'None')
      #return
    #self.COMData = com
    
    ##if self.isValidOverlay('COM') is False:
      ###self.vb.addItem(self.sp)
      ##self.addValidOverlay('COM')
    ##if self.isEnabledOverlay('COM') is False:
      ##return
    ##self.showOverlay('COM')
    #if enabled:
      #self.overlayDict['COM'] = 'None'
      ##self.addDisplayItem('COM', 'None')
      #self.addDisplayItem('COM', 1)
   

