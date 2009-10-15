from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

PAGE_HEIGHT=defaultPageSize[1]
PAGE_WIDTH=defaultPageSize[0]
styles = getSampleStyleSheet()

Title = "Hello world"
pageinfo = "platypus example"

def myFirstPage(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Bold',16)
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, Title)
    canvas.setFont('Times-Roman',9)
    canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo)
    canvas.restoreState()

def myLaterPages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo))
    canvas.restoreState()

def render_pdf_response(summary):
    response = HttpResponse(mimetype="application/pdf")
    response["Content-Disposition"] = "attachment; filename=report.pdf"
    doc = SimpleDocTemplate(response)
    Story = [Spacer(1,2*inch)]
    style = styles["Normal"]
    for layer, stats in summary['statistics'].items():
       label = "Layer %s" % layer
       table = ''.join(["%s: %s" % (k, v[0]) for k, v in stats.items()])
       l = Paragraph(label, style)
       t = Paragraph(table, style)
       Story.append(l)
       Story.append(t)
       Story.append(Spacer(1,0.2*inch))
    doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages)
    return response
