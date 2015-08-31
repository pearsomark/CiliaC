
from debugging import *
from PyQt4 import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl



class GlPlot:
  #def __init__(self, win, pType='render', parent=None):
  def __init__(self, pType='render', parent=None):
    self.plotType = pType
    self.win = gl.GLViewWidget()
    #self.win = win
    QtCore.QObject.connect(self.win, QtCore.SIGNAL('triggered()'), self.closeEvent)
    self.win.setCameraPosition(distance=50)
    #self.glWin = None
    self.glWin = {}
    self.xydim = 0
    self.zScale = 0.3
  
  def closeEvent(self):
    logger.debug('GlPlot::closeEvent()')
    #self.win.close()
    
  def showWindow(self):
    logger.debug('GlPlot::showWindow()')
    self.win.show()
    
  def closeWindow(self):
    logger.debug('GlPlot::closeWindow()')
    self.win.close()

  def setZScale(self, zsc):
    self.zScale = zsc

  def initRenderPlot(self, iSlice, vname):
    logger.debug('GlPlot::initRenderPlot()')
    #self.glWin = 
    x = np.linspace(-12, 12, 50)
    y = np.linspace(-12, 12, 50)
    colors = np.ones((50,50,4), dtype=float)
    colors[...,0] = np.clip(np.cos(((x.reshape(50,1) ** 2) + (y.reshape(1,50) ** 2)) ** 0.5), 0, 1)
    colors[...,1] = colors[...,0]
   
    if vname == 'Anterior':
      self.glWin[vname] = gl.GLSurfacePlotItem(z=iSlice, computedNormals=False, 
                                               smooth=False, shader='shaded', 
                                               color=(0.8, 0.8, 1, 1))
      self.glWin[vname].translate(-40, 0, -20)
    if vname == 'Lateral':
      self.glWin[vname] = gl.GLSurfacePlotItem(z=iSlice, computedNormals=False, 
                                               smooth=False, shader='shaded',
                                               color=(0.6, 0.5, 1, 1))
      self.glWin[vname].translate(-40, 0, -20)
    self.glWin[vname].scale(0.5, 0.5, self.zScale)
    self.win.addItem(self.glWin[vname])
    self.glWin[vname].rotate(110, 0, 0, 1)
    self.isRendered = True

  def updateRenderPlot(self):
    for i in self.glWin.values():
      self.win.removeItem(i)

  def initMeshPlot(self, iSlice):
    self.xydim = len(iSlice[:,0])
    n = self.xydim
    #fSlice = np.float32(iSlice)
    y = np.linspace(0,self.xydim,n)
    x = np.linspace(0,self.xydim,self.xydim)
    for i in range(n):
        yi = np.array([y[i]]*self.xydim)
        z = np.float32(iSlice[:,i])
        pts = np.vstack([x,yi,z]).transpose()
        self.glWin = gl.GLLinePlotItem(pos=pts, color=pg.glColor((i,n*1.3)), width=1.0, antialias=True)
        self.win.addItem(self.glWin)

  def updatePlot(self, iSlice, vname):
    logger.debug('GlPlot::updatePlot()')
    #print('updatePlot() ', self.win)
    if self.plotType == 'render':
      e = np.zeros((128, 128))
      self.glWin[vname].setData(z=e)
      self.glWin[vname].setData(z=iSlice)
    elif self.plotType == 'mesh':
      n = self.xydim
      #fSlice = np.float32(iSlice)
      y = np.linspace(0,self.xydim,self.xydim)
      x = np.linspace(0,self.xydim,self.xydim)
      for i in range(self.xydim):
        yi = np.array([y[i]]*self.xydim)
        z = np.float32(iSlice[:,i])
        pts = np.vstack([x,yi,z]).transpose()
        self.glWin = gl.GLLinePlotItem(pos=pts, color=pg.glColor((i,n*1.3)), width=1.0, antialias=True)
        #self.glWin.setData(pos=pts)
        self.win.addItem(self.glWin[vname])
    else:
      logger.info('Unknown plot type')
      return


class PlotData:
  pass


class DualPlots:
  def __init__(self, conf, **kwargs):
    logger.debug('DualPlots::Init()')
    #self.parent = parent
    self.conf = conf
    self.cData = None
    self.units = 'fr'
    self.viewName = ''
    self.plotType = 'COM'
    for key in kwargs:
      if key == 'cData':
        self.cData = kwargs[key]
      if key == 'units':
        self.units = kwargs[key]
      if key == 'view':
        self.viewName = kwargs[key]
      if key == 'plotType':
        self.plotType = kwargs[key]
    #if cData is not None:
      #self.cData = cData
    self.velocityText = 'test me'
    #if view is not None:
      #if view == 'ANT':
        #self.viewName = 'Anterior'
      #if view == 'LAT':
        #self.viewName = 'Lateral'
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    self.win = pg.GraphicsLayoutWidget()
    #self.win = win
    QtCore.QObject.connect(self.win, QtCore.SIGNAL('triggered()'), self.closeWindow)
    self.win.resize(800,800)
    #self.units = units
    self.measurementUnits = 'fr'
    self.yzero = 0
    self.plots = {1:PlotData(), 2:PlotData()}
    #self.anterior = PlotData()
    #self.lateral = PlotData()
  
  def showPlotWin(self):
    self.win.show()

  def setMeasurementUnits(self, mode):
    logger.debug('DualPlots::setMeasurementUnits(%s)' % mode)
    self.measurementUnits = mode

  def clearPlots(self, viewName):
    #self.plots[viewName].lateralPlot.clear()
    #self.plots[viewName].virticalPlot.clear()
    self.win.clear()

  def addPlots(self, tData, viewNum, viewLabel, t='Movement'):
    logger.debug('DualPlots::addPlots(%s %s)' % (viewNum, self.plotType))
    self.plots[viewNum].track = tData
    if self.plotType == 'Movement':
      self.plots[viewNum].plotData = self.plots[viewNum].track.getTrackingPoints(True)
    else:
      #self.plots[viewName].plotData = self.plots[viewName].track.getCOMRel()
      self.plots[viewNum].plotData = self.plots[viewNum].track.getTrackingPoints()
    if viewNum == 1:
      if self.conf['ShowTitle']:
        if self.conf['LeftPlotTitle'] == 'Default':
          self.win.addLabel(text='%s View' % viewLabel, row=0, col=0)
        else:
          self.win.addLabel(text=self.conf['LeftPlotTitle'], row=0, col=0)
      self.plots[viewNum].lateralPlot = self.win.addPlot(row=1, col=0, title=self.conf['XPlotTitle'])
      self.plots[viewNum].virticalPlot = self.win.addPlot(row=2, col=0, title=self.conf['YPlotTitle'])
    if viewNum == 2:
      if self.conf['ShowTitle']:
        if self.conf['RightPlotTitle'] == 'Default':
          self.win.addLabel(text='%s View' % viewLabel, row=0, col=1)
        else:
          self.win.addLabel(text=self.conf['RightPlotTitle'], row=0, col=1)
      self.plots[viewNum].lateralPlot = self.win.addPlot(row=1, col=1, title=self.conf['XPlotTitle'])
      self.plots[viewNum].virticalPlot = self.win.addPlot(row=2, col=1, title=self.conf['YPlotTitle'])

  def setLabels(self, viewNum):
    logger.debug('DualPlots::setLabels(%s)' % viewNum)
    if (self.measurementUnits == 'mm'):
      self.plots[viewNum].lateralPlot.setLabels(bottom="Seconds", left="Milimeters")
      self.plots[viewNum].virticalPlot.setLabels(bottom="Seconds", left="Milimeters")
    elif (self.measurementUnits == 'fr'):
      self.plots[viewNum].lateralPlot.setLabels(bottom="Frames", left="Pixels")
      self.plots[viewNum].virticalPlot.setLabels(bottom="Frames", left="Pixels")
    
  def makePlot(self, viewNum, viewName, t='Movement'):
    logger.debug('DualPlots::makePlot(%s)' % viewName)
    if self.plots[viewNum].plotData is None or self.units is None:
      logger.error("Missing plot data")
      return
    if self.plotType == 'Movement':
      xdata = self.plots[viewNum].track.getTrackingX(relative=True, scaled=True)
      ydata = self.plots[viewNum].track.getTrackingY(relative=True, scaled=True)
      vdata = None
    else:
      xdata = self.plots[viewNum].track.getTrackingX(relative=True, scaled=True)
      ydata = self.plots[viewNum].track.getTrackingY(relative=True, scaled=True)
      vdata = self.plots[viewNum].track.getVelocitySlopeScaled()
    #print(ydata[0])
    if xdata.shape != ydata.shape:
      logger.error("Wrong shape for plot data")
      return   
    self.showPlot(viewNum, xdata, ydata, vdata)
    if self.plotType == 'Movement':
      xPlaneFit = self.plots[viewNum].track.getYPlaneFit(fit='Movement')
      if xPlaneFit is not None:
        #print('vfit', xPlaneFit)
        self.addToPlot(viewNum, 'xPlane', ydata, xPlaneFit)
    else:
      yPlaneFit = self.plots[viewNum].track.getYPlaneFit()
      xPlaneFit = self.plots[viewNum].track.getXPlaneFit()
      self.addToPlot(viewNum, 'xPlane', ydata, xPlaneFit)
      self.addToPlot(viewNum, 'yPlane', ydata, yPlaneFit)

  #def fixVirtical(self):
    #self.replot(self.measurementUnits)

  def showPlot(self, viewNum, p1Data, p2Data, vdata):
    logger.debug('DualPlots::showPlot(%s)' % viewNum)
    #print(p1Data, p1Data.shape)
    self.setLabels(viewNum)
    self.plots[viewNum].lateralPlot.clear()
    self.plots[viewNum].virticalPlot.clear()
    self.plots[viewNum].lateralPlot.plot(x=p1Data[:,0], y=p1Data[:,1], pen='b')
    self.plots[viewNum].virticalPlot.plot(x=p2Data[:,0], y=p2Data[:,1], pen='b')
    if vdata is not None:
      #self.addVelocityPlotline(p2Data[:,0])
      self.plots[viewNum].virticalPlot.plot(x=p2Data[0:len(vdata),0], y=vdata, pen='g')
    #text = pg.TextItem(self.velocityText, anchor=(-1.5, 0.5), color='000000')
    #self.virticalPlot.addItem(text)
    
  def addToPlot(self, viewNum, pt, d1, d2):
    if d1 is None or d2 is None:
      return
    if len(d1[:,0]) != len(d2):
      print("addToPlot: Invalid shape")
      return
    p = pg.PlotDataItem(x=d1[:,0], y=d2, pen='r')
    if pt == 'yPlane':
      self.plots[viewNum].virticalPlot.addItem(p)
      self.plots[viewNum].virticalPlot.setYRange(min([-3,0, min(d1[:,1])]), max([3.0, max(d1[:,1])]))
    if pt == 'xPlane':
      if self.conf['ShowXFit']:
        self.plots[viewNum].lateralPlot.addItem(p)
      self.plots[viewNum].lateralPlot.setYRange(min([-3,0, min(d2)]), max([3.0, max(d2)]))

  def closeWindow(self):
    #print('Close plot window')
    self.win.hide()

  def closeEvent(self, ev):
    print('evt Close plot window')
  
  def printVirtical(self):
    logger.info('[%s]' % ', '.join(map(str, self.plotData[:,1])))

  def printLateral(self):
    #print(self.plotData[:,1],)
    logger.info('[%s]' % ', '.join(map(str, self.plotData[:,0])))

  def updatePlotData(self):
    self.plotData = self.cData.getCOMRel()
  
  def addVelocityPlotline(self, vs):
    logger.debug('DualPlots::addVelocityPlotline()')
    self.virticalPlot.plot(y=vs, pen='g')
    
  def setVelocityText(self, txt):
    self.velocityText = txt

  def exportPlotAsSVG(self):
    logger.info('DualPlots::exportPlotAsSVG()')
    exporter = pg.exporters.SVGExporter.SVGExporter(self.win.scene())
    exporter.export('/tmp/testplot.svgcla')

  def exportPlotAsPNG(self):
    logger.info('DualPlots::exportPlotAsSVG()')
    exporter = pg.exporters.ImageExporter.ImageExporter(self.virticalPlot)
    exporter.export('/tmp/tmpplot.png')



class XYPlots:
  def __init__(self, view, track):
    logger.debug('XYPlots::Init(%s: %s)' % (view, track))
    self.viewName = view
    self.trackName = track
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    self.win = pg.GraphicsLayoutWidget()
    #self.win = win
    QtCore.QObject.connect(self.win, QtCore.SIGNAL('triggered()'), self.closeWindow)
    self.win.resize(400,800)
    #self.units = units
    self.units = 'fr'
    self.measurementUnits = 'fr'
    self.yzero = 0
    self.plot = PlotData()
  
  def showPlotWin(self):
    self.win.show()

  def setNames(self, view, track):
    self.viewName = view
    self.trackName = track

  def setMeasurementUnits(self, mode):
    logger.debug('XYPlots::setMeasurementUnits(%s)' % mode)
    self.measurementUnits = mode

  def clearPlots(self):
    logger.debug('XYPlots::clearPlots(%s)' % self.viewName)
    self.win.clear()

  def addPlots(self, pData, viewName, t='Movement'):
    logger.debug('XYPlots::addPlots(%s, %s)' % (viewName, t))
    self.plot.data = pData
    self.plot.plotData = self.plot.data.getTrackingPoints(True)
    if self.conf['ShowTltle']:
        self.win.addLabel(text=self.trackName + ': ' + viewName + ' View', row=0, col=0)
    self.plot.lateralPlot = self.win.addPlot(row=1, col=0, title="X movement")
    self.plot.virticalPlot = self.win.addPlot(row=2, col=0, title="Y movement")

  def setLabels(self, viewName):
    logger.debug('XYPlots::setLabels(%s)' % viewName)
    if (self.measurementUnits == 'mm'):
      self.plot.lateralPlot.setLabels(bottom="Seconds", left="Milimeters")
      self.plot.virticalPlot.setLabels(bottom="Seconds", left="Milimeters")
    elif (self.measurementUnits == 'fr'):
      self.plot.lateralPlot.setLabels(bottom="Frames", left="Pixels")
      self.plot.virticalPlot.setLabels(bottom="Frames", left="Pixels")
    
  def makePlot(self, viewName, t='Movement'):
    logger.debug('XYPlots::makePlot(%s, %s)' % (viewName, t))
    if self.plot.plotData is None or self.units is None:
      logger.info("Missing plot data")
      return   
    xdata = self.plot.data.getTrackingX(relative=True, scaled=True)
    ydata = self.plot.data.getTrackingY(relative=True, scaled=True)
    #vdata = self.plot.data.getVelocitySlopeScaled()
    vdata = None
    if xdata.shape != ydata.shape:
      logger.error("Wrong shape for plot data")
      return   
    #xdata = self.fixXData(xdata)
    self.showPlot(viewName, xdata, ydata, vdata)
    xPlaneFit = self.plot.data.getYPlaneFit(fit='Movement')
    self.addToPlot(viewName, 'V', ydata, xPlaneFit)

  def showPlot(self, viewName, p1Data, p2Data, vdata):
    logger.debug('XYPlots::showPlot(%s)' % viewName)
    self.setLabels(viewName)
    self.plot.lateralPlot.clear()
    self.plot.virticalPlot.clear()
    self.plot.lateralPlot.plot(x=p1Data[:,0], y=p1Data[:,1], pen='b')
    self.plot.virticalPlot.plot(x=p2Data[:,0], y=p2Data[:,1], pen='b')
    if vdata is not None:
      #self.addVelocityPlotline(p2Data[:,0])
      self.plot.virticalPlot.plot(x=p2Data[0:len(vdata),0], y=vdata, pen='g')
    
  def addToPlot(self, viewName, pt, d1, d2):
    p = pg.PlotDataItem(x=d1[:,0], y=d2, pen='r')
    if pt == "V":
      self.plot.virticalPlot.addItem(p)
    if pt == "H":
      self.plot.lateralPlot.addItem(p)
      self.plot.lateralPlot.setYRange(min([-5,0, min(d2)]), max([5.0, max(d2)]))

  def closeWindow(self):
    logger.info('XYPlots::closeWindow(%s)' % self.viewName)
    self.win.hide()
  


class SummaryPlot:
  def __init__(self, units='mm', nviews=1):
    logger.debug('SummaryPlot::Init()')
    #self.parent = parent
    self.viewName = 'test'
    self.velocityText = 'nil'
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    #self.win = pg1.GraphicsLayoutWidget()
    #self.win = pg.GraphicsWindow()
    #self.win.resize(600,600)
    self.units = units
    self.measurementUnits = 'mm'
    self.plotData = None
    self.windows = []
    self.plots = []
    self.ySize = 400
    if nviews == 2:
      self.ySize = 300
    #self.win.addLabel(text=self.viewName, row=0, col=0)
    #self.windows.append(pg.GraphicsLayoutWidget())
    #self.plot1 = self.windows[0].addPlot(title="plot1")
    #self.plot1.resize(600, 500)
    #if nviews == 2:
      #self.windows.append(pg.GraphicsLayoutWidget())
      #self.plot2 = self.windows[1].addPlot(title="plot2")
      #self.plot2.resize(600, 500)
    #for i in range(len(self.windows)):
      #exporter = pg.exporters.ImageExporter.ImageExporter(self.windows[i].scene())
      #exporter.export('/tmp/tmpplot%s.png' % i)
  
  def addSummPlot(self, tData, view, vt=None):
    logger.debug('SummaryPlot::addSummPlot()')
    win = pg.GraphicsLayoutWidget()
    win.resize(600,600)
    myPlot = win.addPlot(title=view)
    myPlot.resize(500, self.ySize)
    myPlot.setLabels(bottom="Seconds", left="Milimeters")
    xdata = tData.getTrackingX(units='mm', scaled=True, relative=True)
    ydata = tData.getTrackingY(units='mm', scaled=True, relative=True)
    vdata = tData.getVelocitySlopeScaled(units='mm')
    if xdata.shape != ydata.shape:
      logger.error("Wrong shape for plot data")
      return   
    myPlot.plot(x=ydata[:,0], y=ydata[:,1], pen='b')
    if vdata is not None:
      myPlot.plot(x=ydata[:,0], y=vdata, pen='g')
    xPlaneFit = tData.getYPlaneFit(units='mm')
    myPlot.addItem(pg.PlotDataItem(x=ydata[:,0], y=xPlaneFit, pen='r'))
    if vt is not None:
      text = pg.TextItem(vt, anchor=(-1.5, 0.5), color='000000')
      myPlot.addItem(text) 
    self.plots.append(myPlot)
    self.windows.append(win)
    #self.plotnum += 1

  def exportPlotAsPNG(self):
    logger.debug('SummaryPlot::exportPlotAsSVG()')
    td = mkdtemp()
    #print(td)
    for i in range(len(self.windows)):
      exporter = pg.exporters.ImageExporter.ImageExporter(self.windows[i].scene())
      tdf = os.path.join(td, "plot%d.jpg" % i)
      exporter.export(tdf)
    return td

