
from debugging import *
from dicomdata import DicomInfo
from cdata import CiliaData
from cdisplay import ImageDisplay
from cdata import CiliaData
from cplots import XYPlots
from trackingpoints import TrackingPoints
import dicom
import math
import numpy as np
from scipy import ndimage, stats
import os

class ImageView:
  '''A class that contains information about a View dataset
  '''
  def __init__(self, ui, conf, fname):
    self.ui = ui
    self.conf = conf
    self.filename = str(fname)
    self.ds = None
    self.dcm = None
    self.cData = None
    self.viewPosition = None
    self.viewSeries = None
    self.viewLabel = 'Unknown'
    self.viewNum = 0
    self.imgIndex = 0
    self.lastFrame = 0
    self.isocurve = 0
    self.iMin = None
    self.iMax = None
    self.vLower = None
    self.vUpper = None
    self.disp = None
    self.comROI = False
    #self.addView(self.filename)
    self.comPlot = None
    self.mcomPlot = None
    self.comPlotFlag = False
    self.mcomPlotFlag = False
    self.mtplot = None
    self.measurementUnits = 'fr'
    self.velocityText = ''
    self.overlaysEnabled = True
    self.trackingThreshold = 0.8
    self.trackingBins = 100
    self.freeRotate = 0.0
    self.trackManualType = 'Movement'
    self.plot = {}
    self.track = {}
    self.roi = {}
   
  def resetAll(self):
    logger.debug(' ImageView::resetAll()')
    #if self.comPlotFlag:
      #self.comPlot.closeWindow()
      #self.comPlot = None
      #self.comPlotFlag = False
    self.ds = None
    self.dcm = None
    self.cData = None
    self.viewPosition = None
    self.viewSeries = None
    self.disp.deleteAll()
    self.disp = None
    self.imgIndex = 0
    self.lastFrame = 0
    self.vLower = None
    self.vUpper = None
    self.comROI = False
    self.track = {}
    self.roi = {}
    
  def closeAllPlots(self):
    logger.debug(' ImageView::closeAllPlots()')
    if self.comPlotFlag:
      self.comPlot.closeWindow()
      self.comPlot = None
      self.comPlotFlag = False
    if self.mcomPlotFlag:
      self.mcomPlot.closeWindow()
      self.mcomPlot = None
      self.mcomPlotFlag = False

  def addView(self, fname, gv):
    logger.debug(' ImageView::addView()')
    if fname == "Dummy":
      self.disp = ImageDisplay(self.ui, 'Dummy')
      return
    self.ds = dicom.read_file(fname)
    self.dcm = DicomInfo(self.ds)
    logger.debug('addView: %s', self.dcm)
    if self.dcm is None:
      logger.info('Unsupported DICOM file.')
      self.updateProgressLog('Unsupported DICOM file.')
      return
    self.viewPosition = self.dcm.getViewPosition()
    self.viewSeries = self.dcm.getViewSeries()
    self.viewLabel = self.dcm.getViewLabel()
    self.cData = CiliaData(self.ds, self.dcm)
    self.disp = ImageDisplay(self.ui, gv)
    self.imgIndex = 0
    self.lastFrame = self.dcm.getNumberOfFrames()-1
    v = gv[0:5]+'Title'
    self.viewNum = int(gv[4:5])
    getattr(self.ui, v).setText(self.viewLabel)
    logger.debug('ImageView::addView() %s %s' % (self.viewPosition, self.lastFrame))

  def saveView(self, fname):
    if self.ds is None or self.cData is None:
      return
    pa = self.cData.getPixelArray()
    suid = self.ds.SOPInstanceUID + '.1'
    #self.ds.file_meta.MediaStorageSOPClassUID = 'Secondary Capture Image Storage'
    self.ds.file_meta.MediaStorageSOPInstanceUID = suid
    self.ds.SOPInstanceUID = suid
    self.ds.ImageType = 'DERIVED\\SECONDARY '
    #self.ds.SOPClassUID = 'Secondary Capture Image Storage'
    self.ds.SecondaryCaptureDeviceManufctur = 'Python 2.7.3'
    self.ds.PixelData = pa
    self.ds.save_as(fname)

  def isPrimaryDataset(self):
    if self.ds is None:
      return False
    if 'PRIMARY' in self.ds.ImageType:
      return True
    else:
      return False

  def isValidDataset(self):
    val = False
    if self.dcm is not None:
      val = self.dcm.isValidDataset()
    return val

  def getViewName(self):
    if self.viewPosition is None:
      return 'Unknown'
    if self.viewPosition == 'ANT':
      return 'Anterior'
    if self.viewPosition == 'LAT':
      return 'Lateral'

  def getViewShortName(self):
    return self.viewPosition

  def getViewLabel(self):
    return self.viewLabel

  def getFilename(self):
    return self.filename

  def getShortFilename(self):
    return os.path.basename(self.filename)

  def getImageMinMax(self):
    return self.cData.getImageMinMax()

  def addROI(self, roiType):
    logger.debug(' ImageView::addROI(%s)' % roiType)
    self.makeNewROI(roiType)
    self.disp.addMTROI(self.roi[roiType])

  def removeROI(self, roiType):
    logger.debug(' ImageView::removeROI(%s)' % roiType)
    if roiType in self.roi.keys():
      #self.disp.removeROI(roiType)
      self.disp.removeROI(self.roi[roiType].roi)
      del self.roi[roiType]

  #def addMaskROI(self):
    #logger.info(' ImageView::addMaskROI()')
    #self.makeNewROI('MASK')
    #self.disp.addMTROI(self.roi['MASK'])

  #def removeMaskROI(self):
    ##self.disp.removeMaskROI()
    #if 'MASK' in self.roi.keys():
      #self.disp.removeMaskROI()
      #del self.roi['MASK']

  #def showMaskROI(self):
    ##print(self.cData.getImage().shape)
    #self.disp.showMaskROI(self.cData.getImage())
    
  def applyMaskROI(self, start, end):
    logger.debug(' ImageView::applyMaskROI(%d, %d)' % (start, end))
    if 'MASK' in self.roi.keys():
      roi = self.roi['MASK'].getROICoordinates()
    #roi = self.disp.getMaskROI()
    #print(p, w, h)
    mask = np.ones((256,256))
    mask[roi[0]:roi[1], roi[2]:roi[3]] = 0
    self.cData.maskImage(mask, start, end)

  #def addTrackingROI(self):
    #logger.info(' ImageView::addTrackingROI()')
    #self.makeNewROI('TRACK')
    #self.disp.addMTROI(self.roi['TRACK'])
    ##self.comROI = True
    ##roi = self.disp.addTrackingROI()
    ##self.makeNewROI('TRACK', roi)

  #def removeTrackingROI(self):
    #self.comROI = False
    #self.cData.removeROI()
    #self.disp.removeTrackingROI()

  def showROIPos(self):
    logger.debug(' ImageView::showROIPos()')
    #roi = self.disp.getTrackingROI()
    #roi1 = self.disp.getROIPosition('TRACK')
    for r in self.roi.keys():
      self.roi[r].getROICoordinates()
    
  def addCalibrationROIs(self):
    self.calibROI = True
    self.disp.addCalibrationROIs()

  def updateProgressLog(self, msg):
    self.ui.progressLog.append(msg)

  def getViewFrame(self, imgIndex):
    return self.cData.getImgFrameCopy(imgIndex)

  def setimgIndex(self, num):
    self.imgIndex = num

  def getViewSum(self):
    return self.cData.getImageSum()

  def getDataPointer(self):
    return self.cData

  def getAllUnits(self):
    return self.dcm.getAllUnits()
    
  def getLastFrame(self):
    return self.lastFrame
    
  def rotateData90(self, direction):
    self.cData.modifyArray(direction)

  def rotateData(self, deg):
    self.cData.rotateArray(deg)
    self.updateProgressLog('Rotate Lateral %d degrees' % deg)
    #ff, lf = self.cData.getCOMRange()
    #for n in range(ff, lf):
      #frame = self.cData.getImgFrame(n)
      #frame = ndimage.interpolation.rotate(frame, float(deg))

  def smoothData(self):
    logger.debug(' ImageView::smoothData() %d %d')
    self.cData.modifyArray('SM')
    self.removeCOM()

  def scaleData(self):
    self.cData.modifyArray('SC')

  def setAnalysisLimits(self, frameFrom, frameTo):
    logger.debug(' ImageView::setAnalysisLimits() %d %d' % (frameFrom, frameTo))
    self.cData.setLimits(frameFrom, frameTo)
    if self.comPlotFlag:
      self.comPlot.makePlot(self.viewNum, self.getViewName())

  def removeBackground(self):
    ''' set pixels that are outside the ROI to 0
    '''
    logger.debug(' ImageView:%s:removeBackground()' % self.viewPosition)
    mask = self.makeSummedMask()
    #self.dispA.setDisplayImage(mask)
    self.cData.maskImage(mask)
    self.removeCOM()

  def removeCOM(self):
    logger.debug(' ImageView::removeCOM()')
    for t in self.track.keys():
      self.track[t].removeTrackingPoints()
    #self.cData.deleteCOM()
    self.disp.hideCom()
    self.closeAllPlots()
    self.refreshDisplay(self.imgIndex)

  def makeSummedMask(self):
    '''Make a mask by summing all frames, creating a histogram and using the maximum bin
    '''
    #self.sumData = self.imgData.sum(axis=0)
    sumData = self.cData.getImageSum()
    hist, bins = np.histogram(sumData.ravel(), bins=100)
    mask = sumData > bins[3]
    label_im, nb_labels = ndimage.label(mask)
    sizes = ndimage.sum(mask, label_im, range(nb_labels + 1))
    mean_vals = ndimage.sum(self.cData.getImage(), label_im, range(1, nb_labels + 1))
    mask_size = sizes < max(sizes)
    #print(sizes, mask_size, max(sizes))
    remove_pixel = mask_size[label_im]
    label_im[remove_pixel] = 0
    label_im = ndimage.binary_dilation(label_im)
    return label_im
  
  def getPatientName(self):
    return self.dcm.getPatientName(self.ds)

  def getNameAndSeries(self, hideID):
    return self.dcm.getNameAndSeries(self.ds, hideID)

  def getPatientID(self):
    return self.dcm.getPatientID(self.ds)

  def getReportName(self):
    return self.dcm.getReportName(self.ds)

  def getConversions(self):
    '''Get pixel spacing and frame duration and return formatted string
    '''
    x = self.dcm.getXSpace(1.0)
    y = self.dcm.getYSpace(1.0)
    t = self.dcm.getZSpace(1.0)
    f = self.dcm.getNumberOfFrames()
    return 'Pixel: %1.1f x %1.1fmm  Frame: %ssec x %d' % (x, y, t, f)
  
  def refreshDisplay(self, imgIndex=None):
    logger.debug(' ImageView:%s:refreshDisplay(%s)' % (self.viewLabel, imgIndex))
    if self.disp is None:
      return
    spots = []
    if imgIndex is None:
      imgIndex = self.imgIndex
    self.disp.setDisplayImage(self.cData.getImgFrameCopy(imgIndex), self.iMin, self.iMax)
    for k in self.track.keys():
      if self.track[k].getStatus('visible'):
        #self.disp.addTrackingPoint(self.track[k], self.imgIndex)
        spot = self.track[k].getTrackPointSpot(imgIndex)
        if spot is not None:
          spots.append(spot)
    if len(spots):
      self.disp.showSpots(spots)
    for r in self.roi.keys():
      self.disp.moveTrackingROI(self.roi[r], imgIndex)
    #if 'Moving_ROI' in self.track.keys() and 'TRACK' in self.roi.keys():
      #self.disp.moveTrackingROI(self.roi['TRACK'], imgIndex)

  def showSummedImage(self, sens):
    self.disp.setDisplayImage(self.cData.getRescaledImage(sens))

  def enableOverlay(self, overlayName):
    logger.debug(' ImageView:enableOverlay(%s, %s)' % (self.viewPosition, overlayName))
    if overlayName in self.track.keys():
      self.track[overlayName].setStatus('visible', True)
    for r in self.roi.keys():
      self.roi[r].setStatus('visible', True)
    #self.disp.enableOverlay(item)
    self.refreshDisplay(self.imgIndex)

  def enableOverlays(self):
    logger.debug(' ImageView:%s:enableOverlays()' % self.viewPosition)
    for k in self.track.keys():
      self.track[k].setStatus('visible', True)
    for r in self.roi.keys():
      self.disp.addMTROI(self.roi[r], self.roi[r].roi)
    self.overlaysEnabled = True
    #self.disp.enableOverlays()
    self.refreshDisplay(self.imgIndex)

  def disableOverlay(self, overlayName):
    logger.debug(' ImageView:disableOverlay(%s, %s)' % (self.viewPosition, overlayName))
    if overlayName in self.track.keys():
      self.track[overlayName].setStatus('visible',False)
    #self.disp.disableOverlay(item)
    #self.disp.disableOverlays()
    self.refreshDisplay(self.imgIndex)

  def disableOverlays(self):
    logger.debug(' ImageView:%s:disableOverlays()' % self.viewPosition)
    #self.disp.disableOverlay(item)
    self.overlaysEnabled = False
    for k in self.track.keys():
      self.track[k].setStatus('visible', False)
    for r in self.roi.keys():
      self.roi[r].setStatus('visible', False)
      self.disp.removeROI(self.roi[r].roi)
    #self.disp.disableOverlays()
    self.refreshDisplay(self.imgIndex)

  def trackAuto(self, measurementUnits):
    if self.comROI:
      self.trackFixedROI()
    else:
      self.trackWithoutROI(measurementUnits)

  def invalidateOldCOM(self):
    logger.debug(' ImageView:%s:invalidateOldCOM()' % self.viewPosition)
    for t in self.track.keys():
      self.track[t].deleteVelocityData()
      if t in ('No_ROI', 'Inside_ROI', 'Moving_ROI'):
        self.removeTracking(t)
    if self.comPlotFlag:
      self.comPlot.setVelocityText("")
      self.comPlot.makePlot(self.viewNum, self.getViewName())
    
  def trackWithoutROI(self, measurementUnits):
    '''Find the centre of mass for all slices
    '''
    coms = []
    logger.debug(' ImageView:%s:trackWithoutROI()' % self.viewPosition)
    #for n in range(self.cData.getImgdataLen()):
    ff, lf = self.cData.getCOMRange()
    self.updateProgressLog('%s: Track from %d to %d' % (self.getViewName(), ff, lf))
    for n in range(ff, lf):
      frame = self.cData.getImgFrameCopy(n)
      hist, bins = np.histogram(frame.ravel(), normed=True, bins=100)
      threshold = bins[np.cumsum(hist) * (bins[1] - bins[0]) > 0.8][0]
      mnorm2d = np.ma.masked_less(frame,threshold)
      coms.append(ndimage.measurements.center_of_mass(mnorm2d))
    self.makeNewTracking('No_ROI')
    self.track['No_ROI'].addTrackingPoints(coms, ff, lf)
    #self.cData.saveCOM(coms, ff, lf)
    self.cData.setMeasurementUnits(measurementUnits)

  def trackFixedROI(self):
    logger.debug(' ImageView:%s:trackFixedROI()' % self.viewPosition)
    coms = []
    rois = []
    #roi = self.disp.getTrackingROI()
    if 'TRACK' not in self.roi.keys():
      self.updateProgressLog('Error: Cannot track. No ROI')
      return
    #roi = self.disp.getROIPos('TRACK')
    roi = self.roi['TRACK'].getROICoordinates()
    ff, lf = self.cData.getCOMRange()
    pos, w, h = self.roi['TRACK'].getROIDimensions()
    p = "{0[0]:0.1f},{0[1]:0.1f}".format(pos)
    self.updateProgressLog('%s: ROI: %s  %dx%d Track: %d-%d' % (self.getViewName(), p, w, h, ff, lf))
    #self.updateProgressLog('Track from %d to %d' % (ff, lf))
    for n in range(ff, lf):
      frame = self.cData.getImgFrameCopy(n)
      #mask = np.zeros((128,128))
      mask = np.zeros(self.dcm.getXYMatrixSize())
      mask[roi[0]:roi[1], roi[2]:roi[3]] = 1
      frame[mask == 0] = 0
      hist, bins = np.histogram(frame.ravel(), normed=True, bins=100)
      threshold = bins[np.cumsum(hist) * (bins[1] - bins[0]) > self.trackingThreshold][0]
      mnorm2d = np.ma.masked_less(frame,threshold)
      coms.append(ndimage.measurements.center_of_mass(mnorm2d))
      rois.append(roi)
    self.makeNewTracking('Fixed_ROI')
    self.track['Fixed_ROI'].addTrackingPoints(coms, ff, lf)
    #self.track['Fixed_ROI'].addTrackingROIs(rois, ff, lf)
    self.roi['TRACK'].addTrackingROIs(rois, ff, lf)
    #self.cData.saveCOM(coms, ff, lf)
    #self.cData.saveROI(rois, ff, lf)

  def setTrackingThreshold(self, thr):
    self.trackingThreshold = thr

  def trackMovingROI(self):
    logger.info(' ImageView:%s:trackMovingROI()' % self.viewPosition)
    self.showROIPos()
    coms = []
    rois = []
    #roi = self.disp.getTrackingROI()
    if 'TRACK' not in self.roi.keys():
      self.updateProgressLog('Error: Cannot track. No ROI')
      return
    #roi = self.disp.getROIPos('TRACK')
    self.roi['TRACK'].removeTrackingROIs()
    roi = self.roi['TRACK'].getROICoordinates()
    #if 'Moving_ROI' in self.track.keys():
      #self.track['Moving_ROI'].removeTrackingROIs()
    #self.cData.removeROI()
    xs = roi[1] - roi[0]
    ys = roi[3] - roi[2]
    ff, lf = self.cData.getCOMRange()
    #pos, w, h = self.disp.getROIPosition('TRACK')
    pos, w, h = self.roi['TRACK'].getROIDimensions()
    #print(self.getViewShortName(), pos, roi)
    p = "{0[0]:0.1f},{0[1]:0.1f}".format(pos)
    self.updateProgressLog('%s: ROI: %s  %dx%d Track: %d-%d' % (self.getViewName(), p, w, h, ff, lf))
    #self.updateProgressLog('Track from %d to %d' % (ff, lf))
    for n in range(ff, lf):
      #print('roi:', roi)
      frame = self.cData.getImgFrameCopy(n)
      #mask = np.zeros((128,128))
      mask = np.zeros(self.dcm.getXYMatrixSize())
      mask[roi[0]:roi[1], roi[2]:roi[3]] = 1
      frame[mask == 0] = 0
      #region = self.cData.getImgFrameRegion(n, roi)
      hist, bins = np.histogram(frame.ravel(), normed=True, bins=10)
      #print(bins)
      #print(hist)
      #print(np.cumsum(hist))
      #print(np.cumsum(hist) * (bins[1] - bins[0]))
      #threshold = bins[np.cumsum(hist) * (bins[1] - bins[0]) > 0.05][0]
      bnum = 2
      threshold = bins[bnum]
      mnorm2d = np.ma.masked_less(frame,threshold)
      while not mnorm2d.any() and bnum < 9:
        threshold = bins[bnum]
        mnorm2d = np.ma.masked_less(frame,threshold)
        bnum += 1
      if bnum == 9:
        self.updateProgressLog('Cannot find peak')
      else:
        com = ndimage.measurements.center_of_mass(mnorm2d)
        #print('com: %2.2f, %2.2f:%2.2f' % (threshold, com[0], com[1]))
        coms.append(com)
        p1 = int(com[0] - (roi[1] - roi[0]) / 2)
        p2 = int(com[1] - (roi[3] - roi[2]) / 2)
        roi = (p1, p1+xs, p2, p2+ys)
        rois.append(roi)
      #roi[2] = int(com[1] - roi[3] / 2)
    self.makeNewTracking('Moving_ROI')
    self.track['Moving_ROI'].addTrackingPoints(coms, ff, lf)
    #self.track['Moving_ROI'].addTrackingROIs(rois, ff, lf)
    self.roi['TRACK'].addTrackingROIs(rois, ff, lf)
    #self.cData.saveROI(rois, ff, lf)
    #self.cData.saveCOM(coms, ff, lf)
    self.cData.setMeasurementUnits(self.measurementUnits)

  def setMeasurementUnits(self, measurementUnits):
    logger.debug('ImageView::setMeasurementUnits(%s)' % measurementUnits)
    self.measurementUnits = measurementUnits
    self.cData.setMeasurementUnits(measurementUnits)
    for k in self.track.keys():
      self.track[k].measurementUnits = measurementUnits
    if self.comPlot is not None:
      #self.comPlot.replot(self.measurementUnits)
      self.comPlot.makePlot(self.viewNum, self.getViewName())
    
  def calcVelocityLimits(self, midpoint, ttype):
    logger.debug(' ImageView::calcVelocityLimits(%s %d)' % (ttype, midpoint))
    #lower, upper = self.cData.calcVelocityLimits(midpoint)
    #midpoint = (upper[0] - lower[0]) // 2 + lower[0]
    self.vLower, self.vUpper = self.track[ttype].calcVelocityLimits(midpoint)
    self.updateProgressLog("Velocity limits: %s-%s" % (self.vLower[0], self.vUpper[0]))
    logger.debug('%s:%s %s:%s' % (self.vLower[0], self.vLower[1], self.vUpper[0], self.vUpper[1]))
    self.track[ttype].calcVelocitySlope(self.vLower, self.vUpper)
    
  def calculateVelocity(self, midpoint, latAngle, ttype):
    logger.debug(' ImageView::calculateVelocity(%d, %f)' % (midpoint, latAngle))
    if self.track[ttype].checkCOM() is False:
      self.updateProgressLog('Error: No COM data found')
      return
    self.calcVelocityLimits(midpoint, ttype)
    if self.vUpper[0]-self.vLower[0] < 3:
      self.updateProgressLog("Error: Range too small to calculate velocity")
      return
    d, t, r = self.track[ttype].calculateVelocity(self.dcm, self.vLower[0], self.vUpper[0])
    #self.velocityText = "%2.2f mm/min" % (r)
    self.velocityText = "%s: %2.1fmm in %ssecs = %2.1fmm/min" % (self.viewPosition, d,t,r)
    self.updateProgressLog(self.velocityText)
    if latAngle > 0.0:
      newD = d / math.cos(math.radians(latAngle))
      newV = (newD / t) * 60
      self.updateProgressLog("adjusted d is %2.1f : %2.1fmm/min" % (newD, newV))
    if self.comPlotFlag:
      self.comPlot.setVelocityText(self.velocityText)

  def getVelocityText(self):
    if len(self.velocityText):
      return ['%s Velocity' % self.getViewName(), self.velocityText]
    else:
      return ['', '']

  def showDicomInfo(self):
    if len(self.ds) == 0:
      return
    data = self.dcm.getDicomInfo(self.ds)
    logger.info(data)
    return data

  def plotCentreOfMass(self, plotWin):
    '''Plot horizontal and vertical movement
    '''
    logger.debug(' ImageView::plotCentreOfMass(%s)' % self.comPlotFlag)
    self.comPlot = plotWin
    if self.comPlotFlag == False:
      #nc = self.cData.getCOMRel()
      units = self.dcm.getAllUnits()
      #self.comPlot = DualPlots(self.getDataPointer(), self.getAllUnits(), self.viewPosition)
      if self.comPlot is not None:
        self.comPlot.setMeasurementUnits(self.measurementUnits)
        self.comPlot.setVelocityText(self.velocityText)
        for k in self.track.keys():
          if k in ('No_ROI', 'Fixed_ROI', 'Moving_ROI'):
            self.comPlot.addPlots(self.track[k], self.viewNum, self.viewLabel)
            self.comPlot.makePlot(self.viewNum, self.getViewName())
            self.comPlotFlag = True
    else:
      self.comPlot.closeWindow()
      self.comPlot = None
      self.comPlotFlag = False

  def refreshPlots(self, plotWin):
    logger.debug(' ImageView::refreshPlots(%s)' % plotWin)
    # clear old plot data
    #if self.comPlot is None and self.mcomPlot is None:
      #return
    if self.measurementUnits is None:
      self.measurementUnits = 'fr'
    #nc = self.cData.getCOMRel()
    #units = self.dcm.getAllUnits()
    ##self.comPlot = DualPlots(self.getDataPointer(), self.getAllUnits(), self.viewPosition)
    if self.comPlot is not None:
      self.comPlot.setMeasurementUnits(self.measurementUnits)
      self.comPlot.setVelocityText(self.velocityText)
      #self.comPlot.clearPlots(self.getViewName())
      for k in self.track.keys():
        if k in ('No_ROI', 'Fixed_ROI', 'Moving_ROI'):
          self.comPlot.addPlots(self.track[k], self.viewNum, self.getViewName())
          self.comPlot.makePlot(self.viewNum, self.getViewName())
          self.comPlotFlag = True
    if self.mcomPlot is not None:
      self.mcomPlot.setMeasurementUnits(self.measurementUnits)
      self.mcomPlot.addPlots(self.track[self.trackManualType], self.viewNum, self.getViewName())
      self.mcomPlot.makePlot(self.viewNum, self.getViewName())
      self.mcomPlotFlag = True

  def makeTrackingPlots(self):
    logger.debug(' ImageView::makeTrackingPlots()')
    view = self.getViewName()
    for t in self.track.keys():
      #if not self.track[t].getStatus('ploted'):
      if t not in self.plot.keys() and self.track[t].getStatus('visible'):
        self.plot[t] = XYPlots(self.viewPosition, t)
        #self.manualTrackingPlot(self.plot[t])
        self.plot[t].setMeasurementUnits(self.measurementUnits)
        self.plot[t].addPlots(self.track[t], view, t)
        self.plot[t].makePlot(view, t)
        self.track[t].setStatus('ploted', True)
        self.plot[t].showPlotWin()

  def manualTrackingPlot(self, plotWin):
    logger.debug(' ImageView::manualTrackingPlot(%s)' % self.mcomPlotFlag)
    if self.trackManualType not in self.track.keys():
      return None
    if self.comPlotFlag == False:
      units = self.dcm.getAllUnits()
      self.mcomPlot = plotWin
      if self.mcomPlot is not None:
        self.mcomPlot.setMeasurementUnits(self.measurementUnits)
        self.mcomPlot.addPlots(self.track[self.trackManualType], self.getViewName(), self.trackManualType)
        self.mcomPlot.makePlot(self.getViewName(), self.trackManualType)
        self.mcomPlotFlag = True
    else:
      if self.mcomPlot is not None:
        self.mcomPlot.closeWindow()
        self.mcomPlot = None
        self.mcomPlotFlag = False

  def removePlots(self):
    logger.debug(' ImageView::removePlots() ')
    for p in self.plot.keys():
      self.plot[p].clearPlots()
      self.plot.pop(p, None)

  def printVirtical(self):
    '''Print virtical plot
    '''
    if self.comPlotFlag == True:
      self.comPlot.printVirtical()
    
  def printLateral(self):
    '''Print lateral plot
    '''
    if self.comPlotFlag == True:
      self.comPlot.printLateral()
      
  def straighten(self):
    '''translate data to minimise horizontal drift
    '''
    logger.info('ImageView::straighten() ')
    for k in self.track.keys():
      self.track[k].calcDeviation()
    #(comPolyfit, comPolySlopes) = self.cData.makePolynomialFit(self.getCOMY(True))
    if self.comPlotFlag == True:
      self.comPlot.makePlot(self.viewNum, self.getViewName())

  def getExportData(self):
    logger.debug('ImageView::getExportData %s(%s)' % (self.viewPosition, self.comPlotFlag))
    return self.cData.getCOM(scaled=True)

  def measurePixelSize(self):
    logger.debug('ImageView::measurePixelSize() ')
    if self.calibROI == None:
      return
    roia, roib = self.disp.getCalibrationROIs()
    frame = self.cData.getImgFrameCopy(0)
    mask = np.zeros(self.dcm.getXYMatrixSize())
    mask[roia[0]:roia[1], roia[2]:roia[3]] = 1
    frame[mask == 0] = 0
    hist, bins = np.histogram(frame.ravel(), normed=True, bins=100)
    threshold = bins[np.cumsum(hist) * (bins[1] - bins[0]) > 0.8][0]
    mnorm2d = np.ma.masked_less(frame,threshold)
    posa  = ndimage.measurements.center_of_mass(mnorm2d)
    frame = self.cData.getImgFrameCopy(0)
    mask = np.zeros(self.dcm.getXYMatrixSize())
    mask[roib[0]:roib[1], roib[2]:roib[3]] = 1
    frame[mask == 0] = 0
    hist, bins = np.histogram(frame.ravel(), normed=True, bins=100)
    threshold = bins[np.cumsum(hist) * (bins[1] - bins[0]) > 0.8][0]
    mnorm2d = np.ma.masked_less(frame,threshold)
    posb  = ndimage.measurements.center_of_mass(mnorm2d)
    #print(posa, posb)
    diff = posb[0] - posa[0]
    self.updateProgressLog("Calibration Points: ({0[0]:0.1f},{0[1]:0.1f})  ({1[0]:0.1f},{1[1]:0.1f})".format(posa, posb))
    self.updateProgressLog("{0:0.1f} pixels".format(diff))
    self.disp.showCalibCOM(posa, posb)

  def removeCalibrationROIs(self):
    logger.debug('ImageView::removeCalibrationROIs() ')
    self.disp.removeCalibrationROIs()

  def getSummaryDemographics(self):
    if self.dcm is None:
      return None
    return self.dcm.getDemographicsArray(self.ds)

  def rotateByROI(self):
    logger.debug('ImageView::rotateByROI() ')
    self.disp.addRotateROI(self.iMin, self.iMax)

  def doRotateROI(self, cancel=False, angle=0.0):
    logger.debug('ImageView::doRotateROI() ')
    #angle = 0.0
    if cancel:
      self.disp.removeRotateROI()
      return angle
    if angle == 0.0:
      angle = self.disp.getRotateROI()
    print(angle)
    if angle != 0.0:
      self.updateProgressLog("Rotate %s %0.1f deg" % (self.getViewName(), angle))
      self.cData.rotateArray(angle)
    self.disp.removeRotateROI()
    return angle

  #def measureSizeInsideROI(self):
    #logger.debug('ImageView::measureSizeInsideROI() ')
    #self.makeNewROI('INSIDE')
    #self.disp.addMTROI(self.roi['INSIDE'])
    ##self.disp.addSizeROI()
    
  def doMeasureSizeInsideROI(self, measure):
    roi = 'INSIDE'
    if measure and roi in self.roi.keys():
      x = self.dcm.getXSpace(1.0)
      y = self.dcm.getYSpace(1.0)
      (p, w, h) = self.roi[roi].getROIDimensions()
      #(w, h) = self.disp.getSizeROI()
      self.updateProgressLog("%s: x=%0.1f mm, y= %0.1f mm" % (self.getViewName(), x*w, y*h))
    #self.disp.removeSizeROI()
    self.removeROI(roi)

  def overridePixelSize(self, s):
    self.dcm.setPixelSize(s)

  def setBrightnessContrast(self, fmin, fmax):
    self.iMin = fmin
    self.iMax = fmax

  def addIsocurveROI(self, ia, il):
    logger.info('ImageView::addIsocurveROI(%s, %s, %s) ' % (self.viewPosition, ia, il))
    data = self.cData.getImgFrameCopy(self.imgIndex)
    hist, bins = np.histogram(data.ravel(), bins=50)
    if self.viewPosition == 'ANT':
      self.isocurve = bins[ia]
    if self.viewPosition == 'LAT':
      self.isocurve = bins[il]
    print(self.isocurve)
    self.disp.addIsocurveROI(self.isocurve)
    self.refreshDisplay()

  def showIsocurveValues(self):
    self.updateProgressLog("%s: %0.1f" % (self.getViewName(), self.isocurve))

  def isocurveThreshold(self):
    if self.isocurve == 0:
      return
    ff, lf = self.cData.getCOMRange()
    for n in range(ff, lf):
      frame = self.cData.getImgFrame(n)
      frame[np.where(frame > self.isocurve)] = self.isocurve
    self.disp.removeIsocurveROI()
    self.disp.resetIsocurve()
    self.refreshDisplay()

  def setTrackMouse(self, f, t):
    logger.debug(' ImageView::setTrackMouse() ')
    self.disp.setMouseFlag(f)
    self.trackManualType = t
    if self.trackManualType not in self.track.keys():
      self.makeNewTracking(self.trackManualType)

  def makeNewTracking(self, tt=None, force=False):
    logger.debug(' ImageView::makeNewTracking(%s) ' % tt)
    if tt is None:
      tt = self.trackManualType
    if tt not in self.track.keys() or force == True:
      self.track[tt] = TrackingPoints(tt, self.dcm.getAllUnits(), self.measurementUnits)

  def removeTracking(self, t):
    if t in self.track.keys():
      del self.track[t]

  def makeNewROI(self, rt, roi=None, force=False):
    logger.debug(' ImageView::makeNewROI(%s) ' % rt)
    if rt not in self.roi.keys() or force == True:
      self.roi[rt] = ROIData(rt, roi)
      self.roi[rt].setROISize(self.disp.getPixelSize())

  def getMousePos(self):
    logger.debug(' ImageView::getMousePos() ')
    pos = self.disp.getMousePos()
    if pos[0] > 0 and pos[1] > 0:
      print("%s: %d %2.1f, %2.1f" % (self.getViewName(), self.imgIndex, pos[0], pos[1]))

  def addManualTrackPoint(self):
    logger.debug(' ImageView::addManualTrackPoint() ')
    pos = self.disp.getMousePos()
    if pos[0] > 0 and pos[1] > 0:
      self.track[self.trackManualType].addManualTrackPoint(self.imgIndex, pos[0], pos[1])
      #self.disp.addManualTrackPoint(self.trackManualType, self.imgIndex, pos[0], pos[1])
      #self.disp.addTrackingPoint(self.track[self.trackManualType], self.imgIndex)
      self.refreshDisplay(self.imgIndex)

  def addDummyTrackPoint(self):
    pos = self.disp.getMousePos()

  def getTrackingPoints(self, relative=False):
    logger.debug(' ImageView::getTrackingPoints) %s' % self.getViewName())
    coms = self.track[self.trackManualType].getTrackingPoints(relative)
    return coms

  def trackManualClear(self):
    if self.trackManualType in self.track.keys():
      self.track[self.trackManualType].removeTrackingPoints()
    self.refreshDisplay()

  def trackManualCalcVelocity(self, latAngle):
    (d, t, r) = self.track[self.trackManualType].trackManualCalcVelocity(relative=True, scaled=True)
    if t > 0:
      self.updateProgressLog("%s: %2.1fmm in %ssecs = %2.1fmm/min" % (self.viewPosition, d,t,r))
      if latAngle > 0.0 and self.viewPosition == 'ANT':
        newD = d / math.cos(math.radians(latAngle))
        newV = (newD / t) * 60
        self.updateProgressLog("adjusted d is %2.1f : %2.1fmm/min" % (newD, newV))

  def getTrackingXScaled(self, rel=False):
    return self.track[self.trackManualType].getTrackingX(relative, scaled=True)

  def getManualTrackYScaled(self, rel=False):
    return self.track[self.trackManualType].getTrackingY(relative=rel, scaled=True)

  def saveMetadata(self):
    angle = self.cData.getRotateAngle()
    meta = {'rotate': angle}
    for k in self.track.keys():
      coms = self.track[k].getTrackingPoints()
      if coms is not None:
        meta[k] = coms
    pname = self.filename.replace('.dcm', '.pic')
    #print(meta)
    pickle.dump(meta, open(pname, 'wb'))

  def loadMetadata(self):
    logger.debug(' ImageView:%s:loadMetadata:() ' % self.viewLabel)
    pname = self.filename.replace('.dcm', '.pic')
    try:
      pkl_file = open(pname, 'rb')
    except:
      return
    meta = pickle.load(pkl_file)
    pkl_file.close()
    #print(self.viewPosition, meta['rotate'])
    if meta['rotate'] != 0.0:
      self.doRotateROI(False, meta['rotate'])
    if 'Movement' in meta.keys():
      self.makeNewTracking('Movement')
      self.track['Movement'].setStatus('visible', True)
      for p in meta['Movement']:
        self.track['Movement'].addManualTrackPoint(p[0], p[1], p[2])
    if 'Spiral' in meta.keys():
      self.makeNewTracking('Spiral')
      self.track['Spiral'].setStatus('visible', True)
      for p in meta['Spiral']:
        self.track['Spiral'].addManualTrackPoint(p[0], p[1], p[2])
    self.refreshDisplay(0)

  def getActiveTracking(self):
    return self.track.keys()



class ROIData:
  def __init__(self, roiType, roi=None):
    self.flags = {'visible': True, 'updating': False }
    self.position = (0, 0)
    self.roiType = roiType
    self.roi = roi
    self.roiList = None
    self.calib = (None, None)
    self.ROIFrom = 0
    self.ROITo = 0
    self.startPos = [50, 50]
    self.startSize = (20, 20)
    self.pen = (3,9)
    if roiType == 'MASK':
      self.pen = (0,9)
    
  def setStatus(self, item, flag):
    logger.debug(' ROIData::setStatus(%s, %s, %s)' % (self.roiType, item, flag))
    self.flags[item] = flag

  def updateROI(self, roi):
    self.roi = roi
  
  def getROICoordinates(self):
    pos = self.roi.pos()
    w, h = self.roi.size()
    #print(pos, w, h)
    return (int(pos[0]), int(pos[0])+w, int(pos[1]), int(pos[1])+h)

  def getROIDimensions(self):
    pos = self.roi.pos()
    w, h = self.roi.size()
    print(pos, w, h)
    return (pos, w, h)

  def addTrackingROIs(self, roi, ff, lf):
    self.roiList = np.array(roi)
    self.ROIFrom = ff
    self.ROITo = lf
    #print(self.rois)
    
  def removeTrackingROIs(self):
    if self.roiList is not None:
      del self.roiList
    self.roiList = None
    self.ROIFrom = 0
    self.ROITo = 0

  def hasTrackingROI(self):
    r = False
    if self.roiList is not None:
      r = True
    return r

  def getROIScreenFrame(self, n):
    '''Get ROI data for frame
         ARGS: n: frame number
       RETURN: ROI data for frame or None
    '''
    #print('getCOMScreenFrame()', n, self.COMFrom, self.COMTo)
    if n >= self.ROIFrom and n < self.ROITo:
      return self.roiList[n-self.ROIFrom]
    else:
      return None

  def setROISize(self, psize):
    sz = int(30.0/(psize[0]/2.0))
    #print(psize[0], sz)
    self.startSize = (sz, sz)


