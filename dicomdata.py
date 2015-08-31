
import dicom
import datetime
from debugging import *

class DicomInfo:
  def __init__(self, ds=None, parent=None):
    self.zoom = 1.0
    self.mmPerPixel = [1.0, 1.0]
    self.frames = 0
    self.frameDuration = 1000
    self.largestPixel = 1
    self.orientation = "LS"
    self.matrix = [128, 128]
    self.dataSize = 0
    self.imageID = 'Anterior'
    self.series = None
    self.studyDateTime = None
    self.seriesDateTime = None
    self.seriesDesc = None
    self.dcmData = None
    self.isValid = True
    if ds != None:
      self.updateFromDcm(ds)
      
  def updateFromDcm(self, ds):
    import types
    logger.debug('DicomInfo::updateFromDcm()')
    self.dcmData = ds.pixel_array
    if 'PixelData' in ds:
      self.matrix[0] = int(ds.Rows)
      self.matrix[1] = int(ds.Columns)
      self.dataSize = len(ds.PixelData)
    if 'PixelSpacing' in ds:
      self.mmPerPixel[0] = float(ds.PixelSpacing[0])
      self.mmPerPixel[1] = float(ds.PixelSpacing[1])
    if 'NumberOfFrames' in ds:
      self.frames = ds.NumberOfFrames
      if self.frames <= 1:
        self.isValid = False
        logger.debug('DicomInfo: Insufficient frames %d' % ds.NumberOfFrames)
    else:
      self.frames = len(self.dcmData)
    fd = 0
    if self.frames > 1:
      fd = ds.PhaseInformationSequence[0].ActualFrameDuration
    self.frameDuration = fd
    if 'LargestImagePixelValue' in ds:
      self.largestPixel = ds.LargestImagePixelValue
      if type(self.largestPixel) in types.StringTypes:
        self.largestPixel = ord(ds.LargestImagePixelValue[0])
    if 'ZoomFactor' in ds:
      self.zoom = ds.ZoomFactor
    if 'ImageID' in ds:
      self.imageID = ds.ImageID
    if 'SeriesDescription' in ds:
      self.seriesDesc = ds.SeriesDescription
    self.orientation = ds.DetectorInformationSequence[0].ImageOrientationPatient
    if 'StudyDate' in ds:
      d = ds.StudyDate
      t = ds.StudyTime
      self.studyDateTime = "%s-%s-%s %s:%s" % (d[0:4], d[4:6], d[6:8], t[0:2], t[2:4])
      #dt = datetime.datetime.strptime("%s %s" % (d, t[0:4]), "%Y%m%d %H%M")
      #self.studyDateTime = dt.strftime("%Y-%m-%d %H:%m")
    if 'SeriesDate' in ds:
      d = ds.SeriesDate
      t = ds.SeriesTime
      self.seriesDateTime = "%s-%s-%s %s:%s" % (d[0:4], d[4:6], d[6:8], t[0:2], t[2:4])
      #dt = datetime.datetime.strptime("%s %s" % (d, t[0:4]), "%Y%m%d %H%M")
      #self.seriesDateTime = dt.strftime("%Y-%m-%d %H:%m")
    return 1
      
  def getDicomInfo(self, ds):
    info = '''
Patient's name...: {ptname:s}
Patient id.......: {ptid:s}
Modality.........: {modality:s}
Study Date.......: {sdatetime:s}
Image size.......: {rows:d} x {cols:d}, {size:d} bytes
Pixel spacing....: {x:f} x {y:f} mm
Orientation......: {orientation:s}
Series Desc......: {seriesdesc:s}
ImageID..........: {imageID:s}
Frames...........: {frames:d}
Frame Duration...: {fd:d} msec
Highest Pixel....: {hp:d}
Zoom.............: {zoom:f}'''.format(ptname=ds.PatientName, ptid=ds.PatientID, modality=ds.Modality, 
      sdatetime=self.studyDateTime, rows=self.matrix[0], cols=self.matrix[1], 
      size=self.dataSize, x=self.mmPerPixel[0], y=self.mmPerPixel[1], 
      orientation=self.orientation, seriesdesc=self.seriesDesc, 
      imageID=self.imageID, frames=self.frames, fd=self.frameDuration, 
      hp=self.largestPixel, zoom=self.zoom)
    return info

  def isValidDataset(self):
    return self.isValid

  def printDicomInfo(self, ds):
    logger.info(self.getDicomInfo(ds))

  def getDemographics(self, ds):
    x = self.getXSpace(1.0)
    y = self.getYSpace(1.0)
    t = self.getZSpace(1.0)
    return dict(patientName="%s" % ds.PatientName, 
                patientID="%s" % ds.PatientID, 
                seriesDate="%s" % self.seriesDateTime, 
                orientation=self.orientation, 
                spacing="{0[0]:0.2f}x{0[1]:0.2f} mm per pixel".format([x,y]), 
                matrix="{0[0]:d}x{0[1]:d}".format(self.matrix), 
                duration="{0:d} frames at {1:d} sec per frame".format(self.frames, int(t)), 
                zoom="%s" % self.zoom)

  def getDemographicsArray(self, ds):
    x = self.getXSpace(1.0)
    y = self.getYSpace(1.0)
    t = self.getZSpace(1.0)
    return [["Patient:", "%s" % ds.PatientName], 
            ["ID:", "%s" % ds.PatientID], 
            ["Exam Date:", "%s" % self.seriesDateTime],
            ["Series:", "%s" % self.seriesDesc], 
            ["Spacing:", "{0[0]:0.2f}x{0[1]:0.2f} mm per pixel".format([x,y])], 
            ["Matrix:", "{0[0]:d}x{0[1]:d}".format(self.matrix)], 
            ["Duration:", "{0:d} frames at {1:d} sec per frame".format(self.frames, int(t))], 
            ["Zoom:", "%s" % self.zoom]]

  def getPatientName(self, ds):
    return ds.PatientName

  def getNameAndSeries(self, ds, hideID):
    if hideID:
      return "%s  %s" % (self.seriesDesc, self.seriesDateTime)
    else:
      return "%s  %s %s" % (ds.PatientName, self.seriesDesc, self.seriesDateTime)

  def getViewLabel(self):
    view = self.getViewPosition()
    series = self.getViewSeries()
    dt = datetime.datetime.strptime(self.seriesDateTime, "%Y-%m-%d %H:%M")
    dayTime = dt.strftime("%a %H:%M")
    label = '%s-%s %s' % (view, series, dayTime)
    return label

  def getPatientID(self, ds):
    return ds.PatientID

  def getReportName(self, ds):
    return "%s-%s" % (ds.PatientID, ds.SeriesTime[0:4])

  def getNumberOfFrames(self):
    return self.frames
  
  def getData(self):
    return self.dcmData

  def getAllUnits(self):
    ''' return mm/pixel for x and y, and frame duration in seconds for units mm
        and 1, 1, 1 for units fr
    '''
    logger.debug('DicomInfo::getAllUnits()')
    u = dict(mm={'x':self.mmPerPixel[0], 'y':self.mmPerPixel[1], 't':(self.frameDuration / 1000)},
            fr={'x':1.0, 'y':1.0, 't':1})
    return u
  
  def getUnits(self, mode='mm'):
    logger.debug('DicomInfo::getUnits(%s)' % mode)
    if mode == 'mm':
      return [self.mmPerPixel[0], self.mmPerPixel[1], self.frameDuration / 1000]
    else:
      return [1.0, 1.0, 1]
              
  def getXSpace(self, val, mode='mm'):
    if mode == 'mm':
      return val * self.mmPerPixel[0]
    else:
      return val

  def getYSpace(self, val, mode='mm'):
    if mode == 'mm':
      return val * self.mmPerPixel[1]
    else:
      return val

  def getZSpace(self, val, mode='mm'):
    if mode == 'mm':
      return val * (self.frameDuration / 1000)
    else:
      return val

  def getXYMatrixSize(self):
    return (self.matrix[0],self.matrix[0])

  def getViewPosition(self, short=True):
    view = 'UNKNOWN'
    if self.imageID.lower().find('lateral') != -1:
      if short:
        view = 'LAT'
      else:
        view = 'Lateral'
    if self.imageID.lower().find('anterior') != -1:
      if short:
        view = 'ANT'
      else:
        view = 'Anterior'
    return view

  def getViewSeries(self):
    series = 'Unknown'
    if self.seriesDesc.lower().find('pre') != -1:
      series = 'Pre'
    if self.seriesDesc.lower().find('post') != -1:
      series = 'Post'
    return series

  def fixXunits(self, xdata):
    newx = []
    i = 0
    for x in xdata:
      newx.append([(i * (self.frameDuration / 1000)), x * self.mmPerPixel[0]])
      i += 1
    return newx

  def fixUnits(self, data, xy):
    newarray = []
    i = 0
    fd = self.frameDuration / 1000
    mmp = self.mmPerPixel[1]
    if xy == 'x':
      mmp = self.mmPerPixel[0]
    for d in data:
      newarray.append([i * fd, d * mmp])
      i += 1
    return newarray
      
  def fixUnitss(self, data, xy, units):
    newarray = []
    i = 0
    fd = units[2]
    mmp = units[1]
    if xy == 'x':
      mmp = units[0]
    for d in data:
      newarray.append([i * fd, d * mmp])
      i += 1
    return newarray

  def setPixelSize(self, s):
    self.mmPerPixel[0] = s
    self.mmPerPixel[1] = s

