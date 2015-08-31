from  reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize
#from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, cm
from reportlab.lib import colors
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import _fontdata_enc_winansi
from reportlab.pdfbase import _fontdata_enc_macroman
from reportlab.pdfbase import _fontdata_enc_standard
from reportlab.pdfbase import _fontdata_enc_symbol
from reportlab.pdfbase import _fontdata_enc_zapfdingbats
from reportlab.pdfbase import _fontdata_enc_pdfdoc
from reportlab.pdfbase import _fontdata_enc_macexpert
from reportlab.pdfbase import _fontdata_widths_courier
from reportlab.pdfbase import _fontdata_widths_courierbold
from reportlab.pdfbase import _fontdata_widths_courieroblique
from reportlab.pdfbase import _fontdata_widths_courierboldoblique
from reportlab.pdfbase import _fontdata_widths_helvetica
from reportlab.pdfbase import _fontdata_widths_helveticabold
from reportlab.pdfbase import _fontdata_widths_helveticaoblique
from reportlab.pdfbase import _fontdata_widths_helveticaboldoblique
from reportlab.pdfbase import _fontdata_widths_timesroman
from reportlab.pdfbase import _fontdata_widths_timesbold
from reportlab.pdfbase import _fontdata_widths_timesitalic
from reportlab.pdfbase import _fontdata_widths_timesbolditalic
from reportlab.pdfbase import _fontdata_widths_symbol
from reportlab.pdfbase import _fontdata_widths_zapfdingbats
PAGE_HEIGHT=defaultPageSize[1]


def pdfHeaderFooter(self, canvas, doc):
  snow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
  page_num = canvas.getPageNumber()
  text = "Page #%s   Created on %s" % (page_num, snow)
  canvas.drawRightString(12.5*cm, 28.5*cm, "CiliaC Analysis Report")
  canvas.drawRightString(10*cm, 1*cm, text)

def makeSummary(self, stype):
  logger.debug('StartQT4::makeSummary(%s)' % stype)
  pinfo = self.imageViews[-1].getSummaryDemographics()
  if pinfo is None:
    return

  reportname = self.imageViews[-1].getReportName()+'.pdf'
  filename = QtGui.QFileDialog.getSaveFileName(self, directory=reportname, filter='PDF Files *.pdf(*.pdf);;All Files *(*)')
  #filename = QtGui.QFileDialog.getSaveFileName(self, filter='PDF Files *.pdf(*.pdf);;All Files *(*)')
  if len(filename) == 0:
    return
  doc = SimpleDocTemplate(str(filename), pagesize=A4, rightMargin=1.5*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=3*cm)
  elements = []
  #data = pinfo.items()

  for iv in self.imageViews:
    vt = iv.getVelocityText()
    if stype == 'BOTH' or stype == iv.getViewShortName():
      pinfo.append(vt)
  t=Table(pinfo, rowHeights=12)
  t.setStyle(TableStyle([('BACKGROUND',(1,1),(-2,-2),colors.green),
			('TEXTCOLOR',(0,0),(1,-1),colors.black),
			('ALIGNMENT', (0,0),(0,-1), 'RIGHT')]))

  elements.append(t)
  for iv in self.imageViews:
    if stype == 'BOTH' or stype == iv.getViewShortName():
      drawing = Drawing(400, 280)
      cd = iv.getDataPointer()
      vt = iv.getVelocityText()
      pinfo.append(vt)
      #ydata = cd.getCOMYScaled(False, 'mm').tolist()
      ydata = cd.getCOMYScaled(True, 'mm').tolist()
      xPlaneFit = cd.getYPlaneFit(units='mm', bothAxes=True).tolist()
      vdata = cd.getVelocitySlopeScaled(units='mm', bothAxes=True)
      gdata = [ydata, xPlaneFit]
      if vdata is not None:
	gdata.append(vdata.tolist())
      title = Label()
      title.setOrigin(150, 240)
      title.setText(iv.getViewName())
      ylabel = Label()
      ylabel.setOrigin(0, 100)
      ylabel.angle = 90
      ylabel.setText("Millimeters")
      xlabel = Label()
      xlabel.setOrigin(70, 0)
      xlabel.setText("Seconds")
      lp = LinePlot()
      lp.height = 230
      lp.width = 400
      lp.data = gdata
      lp.lines[0].strokeColor = colors.blue
      lp.lines[1].strokeColor = colors.red
      lp.lines[2].strokeColor = colors.green
      #lp.xValueAxis.xLabel = "Seconds"
      drawing.add(title)
      drawing.add(ylabel)
      drawing.add(xlabel)
      drawing.add(lp)
      elements.append(drawing)

  doc.build(elements, onFirstPage=self.pdfHeaderFooter, onLaterPages=self.pdfHeaderFooter)
  

