#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pdfembed
=========
Embed a pdf inside another.

Dependencies:
    - pdfrw_
    - Reportlab_

.. _pdfrw: https://code.google.com/p/pdfrw/
.. _Reportlab: http://www.reportlab.com/

Based on: https://code.google.com/p/pdfrw/wiki/ExampleTools#Watermarking_PDFs
"""
import os
import sys
import logging

from reportlab.platypus import (PageTemplate, BaseDocTemplate, Frame,
                                NextPageTemplate)
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


logger = logging.getLogger('pdfcrop')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


PAGE_WIDTH, PAGE_HEIGHT = A4


class MyTemplate(PageTemplate):
    def __init__(self, pdf_template_filename, name=None):
        frames = [Frame(
            0.85 * inch,
            0.5 * inch,
            PAGE_WIDTH - 1.15 * inch,
            PAGE_HEIGHT - (1.5 * inch)
        )]

        PageTemplate.__init__(self, name, frames)
        # use first page as template
        page = PdfReader(pdf_template_filename).pages[0]
        self.page_template = pagexobj(page)
        # Scale it to fill the complete page
        self.page_xscale = PAGE_WIDTH/self.page_template.BBox[2]
        self.page_yscale = PAGE_HEIGHT/self.page_template.BBox[3]

    def beforeDrawPage(self, canvas, doc):
        """Draws the background before anything else"""
        canvas.saveState()
        rl_obj = makerl(canvas, self.page_template)
        canvas.scale(self.page_xscale, self.page_yscale)
        canvas.doForm(rl_obj)
        canvas.restoreState()


def merge_pdf(inputfile, outputfile):
    """Create the pdf, with all the contents"""
    if outputfile is None:
        outputfile = 'embed.{0}{1}'.format(*os.path.splitext(inputfile))
    with open(outputfile, 'wb') as f:
        document = BaseDocTemplate(f)
        templates = [MyTemplate(inputfile, name='background')]
        document.addPageTemplates(templates)

        elements = [NextPageTemplate('background')]
        document.multiBuild(elements)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Crop pdf files')
    parser.add_argument('pdf', metavar='pdf', type=str, help='pdf to embed.')
    parser.add_argument('-o', '--output', dest='output',
                        type=str, help='output file')
    parser.add_argument('-l', '--loglevel', dest='loglevel',
                        default='info', type=str, help='Logging level')
    args = parser.parse_args()
    loglevel = getattr(logging, args.loglevel.upper(), logging.INFO)
    logger.setLevel(loglevel)

    merge_pdf(args.pdf, args.output)
