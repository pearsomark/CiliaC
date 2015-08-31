
import math
import numpy as np
from scipy import stats
from debugging import *

class TrackingPoints:
  def __init__(self, trackType, ms, mu):
    self.flags = {'visible': True, 'updating': False, 'ploted': False }
    self.visible = True
    self.updating = False
    self.ploted = False
    self.coms = None
    self.rois = None
    self.trackType = trackType
    self.measurementSizes = ms
    self.measurementUnits = mu
    self.polyfit = None
    self.polySlopes = []
    self.velocityArray = None
    self.velocityLower = 0
    self.velocityUpper = 0
    self.screenOffset = [0.0, 0.0]
    self.COMFrom = 0
    self.COMTo = 0
    self.ROIFrom = 0
    self.ROITo = 0
    self.slope = 0.0
    self.angle = 0.0
    self.comMax = 0
    self.symbol = '+'
    self.symbolSize = 15
    self.symbolColour = 'k'
    if trackType == 'No_ROI':
      self.symbolColour = 'b'
    if trackType == 'Fixed_ROI':
      self.symbolColour = 'g'
    if trackType == 'Moving_ROI':
      self.symbolColour = 'r'
    if trackType == 'Movement':
      self.symbolColour = 'c'
    if trackType == 'Spiral':
      self.symbolColour = 'm'

  def setUnits(self, units):
    self.units = units

  def setMeasurementUnits(self, mu):
    self.units = mu

  def setSymbol(self, sym, size, colour):
    self.symbol = sym
    self.symbolSize = size
    self.symbolColour = colour

  def setStatus(self, item, flag):
    logger.debug(' TrackingPoints::setStatus(%s, %s, %s)' % (self.trackType, item, flag))
    self.flags[item] = flag

  def getStatus(self, item):
    return self.flags[item]

  def getTrackingType(self):
    return self.trackType

  def addManualTrackPoint(self, f, x, y):
    logger.debug(' TrackingPoints::addManualTrackPoint(%d, %2.1f, %2.1f)' % (f, x, y))
    if self.coms is None:
      self.coms = np.array([[f, x, y]])
    else:
      if f in self.coms[:,0]:
        i = np.where(self.coms[:] == f)[0][0]
        self.coms[i] = [f, x, y]
      else:
        self.coms = np.vstack((self.coms,[f, x, y]))
    #self.mcoms = np.sort(self.mcoms, axis=0)
    self.coms = self.coms[self.coms[:,0].argsort()]

  def getManualTrackPoint(self, f):
    logger.debug(' TrackingPoints::getManualTrackPoint(%d)' % (f))
    r = None
    if self.coms is not None:
      if f in self.coms[:,0]:
        i = np.where(self.coms[:] == f)[0][0]
        #print(self.mcoms[i])
        r = self.coms[i]
    return r

  def getTrackPointSpot(self, f):
    logger.debug(' TrackingPoints::getTrackPointSpot(%s %d)' % (self.trackType, f))
    spot = None
    if self.coms is not None and self.flags['visible']:
      if f in self.coms[:,0]:
        i = np.where(self.coms[:] == f)[0][0]
        #r = self.coms[i]
        if self.coms[i][0] == f:
          spot = {'pos':(self.coms[i][1],self.coms[i][2]), 'symbol':self.symbol,
                  'size':self.symbolSize, 'pen':self.symbolColour}
    return spot

  def getTrackingPoints(self, relative=False):
    logger.debug(' TrackingPoints::getTrackingPoints()')
    if self.coms is None:
      return None
    y = self.getTrackingY(relative=True, scaled=False)[:,1]
    #print('Y', y)
    if len(y) > 5:
      (self.polyfit, self.polySlopes) = self.makePolynomialFit(y)
    #print(self.mcoms)
    return self.coms

  def removeTrackingPoints(self):
    logger.debug(' TrackingPoints::removeTrackingPoints()')
    if self.coms is not None:
      del self.coms
      self.coms = None

  def getTrackingX(self, **kwargs):
    '''
    Return the x coordinates of the current tracking
    kwargs: scaled - scale according to units
            relative - make all values relative to point 0
            units - force units to be mm or fr
    '''
    logger.debug(' TrackingPoints::getTrackingX(%s)' % kwargs)
    measurementUnits = self.measurementUnits
    if 'units' in kwargs.keys():
      measurementUnits = kwargs['units']
    if 'scaled' in kwargs.keys() and kwargs['scaled']:
      multiplier = self.measurementSizes[measurementUnits]
    else:
      multiplier = self.measurementSizes['fr']
    if 'relative' in kwargs.keys() and kwargs['relative']:
      a0 = (self.coms[:,0]-self.coms[0,0]) * multiplier['t']
      a1 = (self.coms[:,1]-self.coms[0,1]) * multiplier['y']
      #return np.array(zip(self.mcoms[:,0]-self.mcoms[0,0], self.mcoms[:,1]-self.mcoms[0,1]))
      return np.array(zip(a0, a1))
    else:
      return np.array(zip(self.coms[:,0] * multiplier['t'], self.coms[:,1] * multiplier['y']))

  def getTrackingY(self, **kwargs):
    '''
    Return the y coordinates of the current tracking
    kwargs: scaled - scale according to units
            relative - make all values relative to point 0
            units - force units to be mm or fr
    '''
    logger.debug(' TrackingPoints::getTrackingY(%s)' % kwargs)
    measurementUnits = self.measurementUnits
    if 'units' in kwargs.keys():
      measurementUnits = kwargs['units']
    if 'scaled' in kwargs.keys() and kwargs['scaled']:
      multiplier = self.measurementSizes[measurementUnits]
    else:
      multiplier = self.measurementSizes['fr']
    if 'relative' in kwargs.keys() and kwargs['relative']:
      a0 = (self.coms[:,0]-self.coms[0,0]) * multiplier['t']
      a1 = (self.coms[:,2]-self.coms[0,2]) * multiplier['y']
      return np.array(zip(a0, a1))
    else:
      return np.array(zip(self.coms[:,0] * multiplier['t'], self.coms[:,2] * multiplier['y']))

  def checkCOM(self):
    if self.coms is None:
      return False
    else:
      return True

  #def getComX(self):
    #logger.debug(' TrackingPoints::getComX')
    #if self.coms is None:
      #return None
    #else:
      #return self.coms[:,1]

  #def getComY(self, relative=False):
    #logger.debug(' TrackingPoints::getComY')
    #if self.coms is None:
      #return None
    #else:
      #a = self.coms[:,1]
      ##print (a.shape)
      #if relative:
        #return a - a[0]
      #else:
        #return a

  def getVisibility(self):
    return self.visible

  def getUpdating(self):
    return self.updating

  def getLimits(self, axis, units=None):
    pass

  def trackManualCalcVelocity(self, relative=True, scaled=True):
    logger.debug(' TrackingPoints::trackManualCalcVelocity()')
    if self.coms is None:
      return (0, 0, 0)
    if scaled:
      multiplier = self.measurementSizes['mm']
    else:
      multiplier = self.measurementSizes['fr']
    if relative:
      a0 = (self.coms[:,0]-self.coms[0,0]) * multiplier['t']
      a1 = (self.coms[:,2]-self.coms[0,2]) * multiplier['y']
    else:
      a0 = (self.coms[:,0]) * multiplier['t']
      a1 = (self.coms[:,2]) * multiplier['y']
    time = a0[-1] - a0[0]
    distance = a1[-1] - a1[0]
    rate = (distance / time) * 60
    #print("%2.1fmm in %dsec" % (distance, time))
    return (distance, time, rate)

  def makePolynomialFit(self, yData=None):
    ''' calculate 4th order polynomial fit '''
    logger.debug('TrackingPoints::makePolynomialFit()')
    if yData is None:
      return
    #y = self.getCOMY(True)
    y = yData
    x = np.array(range(len(y)))
    coeffs = np.polyfit(x, y, 4)
    f = np.poly1d(coeffs)
    y_new = np.linspace(x[0], x[-1], len(y))
    #self.comPolyfit = f(y_new)
    polyfit = f(y_new)
    h = 0.1
    slopes = []
    for a in range(len(x)):
      fprime = (f(a+h)-f(a))/h # derivative
      tan = f(a)+fprime*(x-a)  # tangent
      slope = stats.linregress(x, tan)[0]
      #print(a, self.comPolyfit[a])
      slopes.append([slope, polyfit[a]])
    return (polyfit, np.array(slopes))

  def makeStraightlineFit(self, y, zeroIntersect = False):
    logger.debug('TrackingPoints::makeStraightlineFit()')
    #print(y)
    x = np.array(range(len(y)))
    slope, intercept, r_value, p_value, slope_std_error = stats.linregress(x, y)
    # Calculate some additional outputs
    predict_y = intercept + slope * x
    #print ('slope: %f, intercept: %f' % (slope, intercept))
    #self.yzero = predict_y[0]
    pred_error = y - predict_y
    degrees_of_freedom = len(x) - 2
    residual_std_error = np.sqrt(np.sum(pred_error**2) / degrees_of_freedom)
    #print("dof: %s, p1:%s,  p2:%s" % (degrees_of_freedom, predict_y[0], predict_y[-1]))
    #a = abs(predict_y[0]) + abs((predict_y[-1])
    a = abs(predict_y[-1]-predict_y[0])
    b = float(len(y))
    c = self.triangleSide(a, b, 90)
    #print('a:%s b:%s c:%s' % (a, b, c))
    #print("line fit angle: %fdeg" % math.degrees(self.triangleAngle(b, c, a)))    
    if zeroIntersect:
      return slope, self.triangleAngle(b, c, a), predict_y, y - predict_y[0]
    else:
      return slope, self.triangleAngle(b, c, a), predict_y
   
  def triangleSide(self, a, b, t):
    return math.sqrt(a**2 + b**2 - (2.0 * a * b * math.cos(math.radians(t))))
  
  def triangleAngle(self, a, b, c):
    return math.acos((c**2 - b**2 - a**2)/(-2.0 * a * b))

  #def getVirtFit(self, units=None, bothAxes=False, fit='COM'):
    #''' return scaled virtical fit data '''
    #logger.debug('TrackingPoints::getVirtFit()')
    #poly = self.polyfit
    #if poly is None:
      #return None
    #if units is None:
      #multiplier = self.measurementSizes[self.measurementUnits]
    #else:
      #multiplier = self.measurementSizes[units]
    ##units = self.dcm.getAllUnits()
    #if bothAxes:
      #x = np.array(range(len(poly))) * multiplier['t']
      #return np.array(zip(x, (poly * multiplier['y'])))
    #else:
      #return poly * multiplier['y']

  def addTrackingPoints(self, com, ff, lf):
    '''Subtract x[0] from all x values and y[0] from all y values
       and save as numpy array. Also store screen offset
       ARGS: com: array of datapoints
              ff: first frame of array
              lf: last frame of array
       RETURN: Nil
    '''
    coms = np.array(com)
    logger.debug(' TrackingPoints::addTrackingPoints() %s %s %s' % (ff, lf, coms.shape))
    self.screenOffset = com[0]
    self.coms = np.array(zip(range(ff, lf), coms[:,0], coms[:,1]))
    #print(self.screenOffset, self.coms)
    self.COMFrom = ff
    self.COMTo = lf
    #(self.polyfit, self.polySlopes) = self.makePolynomialFit(self.getComY(relative=True))
    if self.comMax < max(self.coms[:,1]):
      self.comMax = max(self.coms[:,1])
    #self.slope, self.angle, self.xPlaneFit =  self.makeStraightlineFit(self.getComX())
    
  def calcVelocitySlope(self, vLower, vUpper):
    '''Calculate straight line y values for velocity between COMfrom and COMto
    '''
    logger.debug(' TrackingPoints::calcVelocitySlope(%d, %d: %d, %d)' % (vLower[0], vLower[1], vUpper[0], vUpper[1]))
    arr = []
    slope = (vUpper[1] - vLower[1]) / (vUpper[0] - vLower[0])
    intercept = vLower[1] - (vLower[0] * slope)
    limit = self.comMax + 1.5
    for i in range(0, (self.COMTo - self.COMFrom) , 1):
      yval = i * slope + intercept
      if yval < limit:
        arr.append(yval)
      #else:
        #arr.append(0)
    self.velocityArray = np.array(arr)
    
  def getVelocitySlope(self):
    return self.velocityArray

  def getVelocitySlopeScaled(self, units=None, bothAxes=False):
    logger.debug(' TrackingPoints::getVelocitySlope()' )
    if self.velocityArray is None:
      return None
    if units is None:
      multiplier = self.units[self.measurementUnits]
    else:
      multiplier = self.units[units]
    if bothAxes:
      x = np.array(range(len(self.velocityArray))) * multiplier['t']
      return np.array(zip(x, (self.velocityArray * multiplier['y'])))
    else:
      return self.velocityArray * multiplier['y']

  def getXPlaneFit(self, relative=True, scaled=True):
    ''' return scaled x plane fit data '''
    logger.debug('TrackingPoints::getXPlaneFit()')
    slope, angle, fit = self.makeStraightlineFit(self.getTrackingX(relative=relative, scaled=scaled)[:,1])
    #print("fit angle: %f" % math.degrees(angle))
    if fit is None:
      return False
    #return (xPlaneFit * self.measurementSizes[self.measurementUnits]['x'])
    return fit

  def getYPlaneFit(self, units=None, bothAxes=False, fit='COM'):
    ''' return scaled y plane fit data '''
    logger.debug('TrackingPoints::getYPlaneFit()')
    (polyfit, polySlopes) = self.makePolynomialFit(self.getTrackingY(relative=True, scaled=True)[:,1])
    return polyfit

  def calcVelocityLimits(self, midpoint):
    logger.debug('TrackingPoints::calcVelocityLimits(%d)' % (midpoint))
    if self.polyfit is None:
      self.getTrackingPoints()
    if self.polyfit is None:
      logger.error("Invalid polynomial")
      return (0, 0)
    y = self.polyfit
    tol = 25
    #midpoint = 30
    slopes = self.polySlopes[:,0]
    #print(slopes)
    avg = slopes[midpoint]
    #print(midpoint, "%f" % avg)
    up_frame = midpoint; down_frame = midpoint
    up_slope = avg; down_slope = avg
    up_slope_diff = 0; down_slope_diff = 0
    up_count = 0; down_count = 0; loop_count = 0
    #last_frame = self.numFrames
    last_frame = self.COMTo - self.COMFrom
    while down_frame > 0 and up_frame < last_frame-1 and loop_count < last_frame:
      loop_count += 1
      if up_frame < last_frame and up_slope_diff <= tol:
        up_frame += 1; up_count += 1
        up_slope = slopes[up_frame]
      if down_frame > 0 and down_slope_diff <= tol:
        down_frame -= 1; down_count += 1
        down_slope = slopes[down_frame]
      avg = sum(slopes[down_frame:up_frame]) / (up_count + down_count)
      #print(avg)
      if avg < 0.001:
        up_slope_diff = 1
        down_slope_diff = 1
      else:
        up_slope_diff = abs((avg-up_slope) / avg * 100)
        down_slope_diff = abs((avg-down_slope) / avg * 100)
      #print(avg, up_frame, up_slope_diff, down_frame, down_slope_diff)
    self.velocityLower = down_frame+1
    self.velocityUpper = up_frame-1
    logger.debug("Velocity limits: %s-%s" % (self.velocityLower, self.velocityUpper))
    return [self.velocityLower, self.polySlopes[self.velocityLower,1]], [self.velocityUpper, self.polySlopes[self.velocityUpper,1]]

  def calculateVelocity(self, dcm, velocityLower=0, velocityUpper=0):
    logger.debug('TrackingPoints::calculateVelocity(%d, %d)' % (velocityLower, velocityUpper))
    if velocityLower == 0 or velocityUpper == 0:
      logger.error("TrackingPoints::calculateVelocity() Invalid limits %d %d" % (velocityLower, velocityUpper))
      return
    x = velocityUpper - velocityLower
    y = self.polySlopes[velocityUpper,1] - self.polySlopes[velocityLower,1]
    #logger.debug(self.comPolySlopes[velocityUpper,1], self.comPolySlopes[velocityLower,1])
    distance = dcm.getYSpace(y, 'mm')
    time = dcm.getZSpace(x, 'mm')
    rate = (distance / time) * 60
    return distance, time, rate 
    #print("%smm in %ssecs = %smm/min" % (distance, time, rate))

  def calcVelocitySlope(self, vLower, vUpper):
    '''Calculate straight line y values for velocity between COMfrom and COMto
    '''
    logger.debug(' TrackingPoints::calcVelocitySlope(%d, %d: %d, %d)' % (vLower[0], vLower[1], vUpper[0], vUpper[1]))
    arr = []
    slope = (vUpper[1] - vLower[1]) / (vUpper[0] - vLower[0])
    intercept = vLower[1] - (vLower[0] * slope)
    limit = self.comMax + 1.5
    for i in range(0, (self.COMTo - self.COMFrom) , 1):
      yval = i * slope + intercept
      if yval < limit:
        arr.append(yval)
      #else:
        #arr.append(0)
    self.velocityArray = np.array(arr)
    
  def getVelocitySlope(self):
    return self.velocityArray

  def getVelocitySlopeScaled(self, units=None, bothAxes=False):
    logger.debug(' TrackingPoints::getVelocitySlope()')
    if self.velocityArray is None:
      return None
    if units is None:
      multiplier = self.measurementSizes[self.measurementUnits]
    else:
      multiplier = self.measurementSizes[units]
    if bothAxes:
      x = np.array(range(len(self.velocityArray))) * multiplier['t']
      return np.array(zip(x, (self.velocityArray * multiplier['y'])))
    else:
      return self.velocityArray * multiplier['y']

  def deleteVelocityData(self):
    self.velocityArray = None

  def straightenData(self, data, angle):
    ref_angle = math.radians(0.5)
    logger.debug(" TrackingPoints::straightenData %f" % ref_angle)
    dx = data[:,0]; dy = data[:,1]
    slope, angle, lateralfit =  self.makeStraightlineFit(dx, False)
    logger.info("Start angle: %f deg" % math.degrees(angle))
    if angle < ref_angle:
      logger.info("angle is < 0.5deg")
      return data
    ta = angle / 2.0
    dx = dx - lateralfit[0]
    #newAngle = angle
    while angle > ref_angle:
      cosTheta = math.cos(angle)
      sinTheta = math.sin(angle)
      if self.slope < 0.0:
        cosTheta = math.cos(math.pi*2.0 - angle)
        sinTheta = math.sin(math.pi*2.0 - angle)
      #print("ta: %s ct: %s st: %s" % (ta, cosTheta, sinTheta))
      tdx = dx * cosTheta + dy * sinTheta
      tdy = dx * sinTheta + dy * cosTheta
      slope1, newAngle, lateralfit =  self.makeStraightlineFit(tdx, False)
      #print("1 slope: %s  ta: %s  newAngle: %s " % (slope1, math.degrees(ta), math.degrees(newAngle)))
      dx = dx - lateralfit[0]
      if abs(newAngle) > ref_angle:
        #print("case2")
        tdx = dx * cosTheta - dy * sinTheta
        tdy = dx * sinTheta + dy * cosTheta
      slope, newAngle, lateralfit =  self.makeStraightlineFit(tdx, False)
      #print("2 slope: %s  ta: %s  newAngle: %s " % (slope, math.degrees(ta), math.degrees(newAngle)))
      dx = dx - lateralfit[0]
      #print(slope - slope1)
      if abs(newAngle) > angle:
        logger.warn("Angle is increasing")
        break
      angle = newAngle
      ta = angle / 2.0
      dx = tdx
      dy = tdy
    logger.debug("Angle is %f" % math.degrees(angle))
    multiplier = self.measurementSizes[self.measurementUnits]
    return np.array(zip((dx * multiplier['t']),dy))
  
  def calcDeviation(self):
    logger.debug(' TrackingPoints::calcDeviation(%s)' % self.trackType)
    xy = np.delete(self.getTrackingPoints(), 0, 1)
    #xy = np.array(zip(tp[:,1],tp[:,2]))
    slope, angle, fit = self.makeStraightlineFit(xy[:,0])
    coms = self.straightenData(xy, angle)
    self.coms = np.array(zip(self.coms[:,0], coms[:,0], coms[:,1]))
    slope, angle, xPlaneFit =  self.makeStraightlineFit(self.coms[:,1])
    logger.info("final angle: %f" % math.degrees(angle))

