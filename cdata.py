
import numpy as np
from scipy import ndimage, stats
from debugging import *

class CiliaData:
  def __init__(self, ds, dcm):
    self.ds = ds
    self.dcm = dcm
    self.dcmData = self.ds.pixel_array
    self.imgData = np.float32(self.dcm.getData())
    self.imgIndex = 0
    self.numFrames = self.dcm.getNumberOfFrames()
    self.coms = None
    self.cscoms = {'Movement': None, 'Spiral': None}
    self.rois = None
    self.comPolyfit = None
    self.mcomPolyfit = None
    self.coeffs = []
    self.comPolySlopes = []
    self.mcomPolySlopes = []
    self.velocityArray = None
    self.tolerance = 25
    self.xPlaneFit = None
    self.velocityfit = None
    self.measurementUnits = 'fr'
    self.deviations = None
    self.yzero = 0
    self.angle = 0.0
    self.freeRotate = 0.0
    self.screenOffset = [0.0, 0.0]
    self.units = self.dcm.getAllUnits()
    self.frameFrom = 0
    self.frameTo = self.numFrames - 1
    self.COMFrom = 0
    self.COMTo = self.numFrames - 1
    self.ROIFrom = 0
    self.ROITo = 0
    self.comMax = 0
    self.velocityUpper = 0
    self.velocityLower = 0

  def modifyArray(self, cmd):
    '''Rotate, scale or smooth data where cmd is one of  'RR' 'RL' 'SM' 'SC'
    '''
    if self.dcmData is None:
      return
    self.coms = None
    if cmd == "RL":
      self.imgData = np.array([np.rot90(self.imgData[n]) for n in range(self.numFrames)])
    if cmd == "RR":
      self.imgData = np.array([np.rot90(self.imgData[n], k=3) for n in range(self.numFrames)])
    self.xPlaneFit = None
    if cmd == "SM":
      self.imgData = np.array([ndimage.gaussian_filter(self.imgData[n], sigma=0.5) for n in range(self.numFrames)])
    if cmd == "SC":
      newmax = 128.0
      oldmax = self.imgData.max()
      self.imgData = self.imgData / oldmax * newmax

  def getPixelArray(self):
    if self.dcmData is None:
      return None
    imd = np.array(self.imgData, dtype=np.uint16)
    return imd.tostring()

  #def updatePixelArray(self):
    #if self.dcmData is None:
      #return
    #imd = np.array(self.imgData, dtype=np.uint16)
    ##imd = self.imgData.view('float16')
    #print(imd.dtype)
    ##imd[:,:,:] = self.imgData
    #self.ds.PixelData = imd.tostring()

  def rotateArray(self, deg):
    logger.debug(' CiliaData::rotateArray(%s)' % deg)
    self.freeRotate += deg
    for n in range(self.frameFrom, self.numFrames, 1):
      f = self.imgData[n]
      #print(n)
      fp = ndimage.rotate(f, float(deg), reshape=True)
      so = f.shape[0]
      sn = fp.shape[0]
      dl = int((sn - so) / 2)
      dh = dl
      if sn - (dl + dl) > so:
        dh += 1
      self.imgData[n] = fp[dl:-dh, dl:-dh]

  def getRotateAngle(self):
    return self.freeRotate

  def setMeasurementUnits(self, u):
    '''Set measurement units where units are 'mm' or 'fr' 
    '''
    logger.debug(' CiliaData::setMeasurementUnits(%s)' % u)
    self.measurementUnits = u
    
  def setLimits(self, lfrom, lto):
    logger.debug(' CiliaData::setLimits() %d %d' % (lfrom, lto))
    self.frameFrom = lfrom
    self.frameTo = lto
    #if self.coms is not None:
      #(self.comPolyfit, self.comPolySlopes) = self.makePolynomialFit(self.getTrackingY(relative=True)[:,1])
      #self.slope, self.angle, self.xPlaneFit =  self.makeStraightlineFit(self.getCOMX())
    
  def getImgdataLen(self):
    '''Return Z length of image data '''
    return len(self.imgData)
  
  def getImgFrame(self, n):
    '''Return frame 'n' '''
    return self.imgData[n]
  
  def getImgFrameCopy(self, n):
    '''Return frame 'n' '''
    return self.imgData[n].copy()
  
  def getImgFrameRegion(self, n, roi):
    '''Return region of frame 'n' '''
    logger.debug(' CiliaData::getImgFrameRegion() %d %d:%d %d:%d' (n, roi[0],roi[1], roi[2],roi[3]))
    return self.imgData[n][roi[0]:roi[1], roi[2]:roi[3]]
  
  def getImageFrameMax(self, n):
    '''Return the maximun pixel value from frame 'n' '''
    return self.imgData[n].max()
  
  def getImage(self):
    '''Return all image data '''
    return self.imgData
  
  def getImageMinMax(self):
    '''Return min and max pixel in image '''
    return (self.imgData.min(), self.imgData.max())
  
  def getImageSum(self):
    '''return summed image along the Z axis '''
    return self.imgData.sum(axis=0)
  
  def getRescaledImage(self, sens):
    '''return summed image along the Z axis '''
    img = self.imgData.mean(axis=0)
    hist, bins = np.histogram(img.ravel(), normed=True, bins=10)
    #print(bins)
    if sens == 0:
      return img
    img[np.where(img > bins[sens])] = bins[sens]
    return img
  
  def maskImage(self, mask, start=None, end=None):
    '''Apply the mask 'mask' to frames 'start' to 'end'
    The result is stored in imgData
    '''
    logger.debug(' CiliaData::maskImage() %s %s' % (start, end))
    if start is None:
      start = 0
    if end is None:
      end = len(self.imgData)
    for n in range(start, end):
      frame = self.imgData[n]
      frame[mask == 0] = 0
      self.imgData[n] = frame
    
  def getCOMRange(self):
    '''First and last frame+1 for use in range statements
    '''
    logger.debug(' CiliaData::getCOMRange() %d %d' % (self.frameFrom, self.frameTo+1))
    return self.frameFrom, self.frameTo+1
    
  def getCOMLimits(self):
    logger.debug(' CiliaData::getCOMLimits() %d %d' % (self.frameFrom, self.frameTo))
    return self.frameFrom, self.frameTo
    
  def saveROI(self, roi, ff, lf):
    self.rois = np.array(roi)
    self.ROIFrom = ff
    self.ROITo = lf
    #print(self.rois)
    
  def getROI(self, scaled=False):
    '''Return array containing roi for each frame
    '''
    print('getROI', scaled)
    return self.rois
    #if scaled:
      #x = self.getROIX() * self.units[self.measurementUnits]['x']
      #y = self.getROIY() * self.units[self.measurementUnits]['y']
      #return np.array(zip(x, y))
    #else:
      #return self.rois

  def removeROI(self):
    if self.rois is not None:
      del self.rois
    self.rois = None
    self.ROIFrom = 0
    self.ROITo = 0

  def getROIScreenFrame(self, n):
    '''Get ROI data for frame or None
         ARGS: n: frame number
       RETURN: ROI data for frame or None
    '''
    #print('getCOMScreenFrame()', n, self.COMFrom, self.COMTo)
    if n >= self.ROIFrom and n < self.ROITo:
      return self.rois[n-self.ROIFrom]
    else:
      return None
    

