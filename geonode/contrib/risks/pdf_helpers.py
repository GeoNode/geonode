#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import subprocess
from StringIO import StringIO

from django.conf import settings

from geonode.utils import run_subprocess

log = logging.getLogger(__name__)


def generate_pdf_weasyprint_api(urls, pdf):
    from weasyprint import HTML
    h = HTML(urls[0])
    h.write_pdf(pdf)
    return pdf


def generate_pdf_wkhtml2pdf(urls, pdf):
    converter_path = settings.RISKS['PDF_GENERATOR']['BIN']
    converter_opts = settings.RISKS['PDF_GENERATOR']['ARGS']
    args = [converter_path] + converter_opts + urls + [ pdf]
    log.info('running pdf converter with args: %s', args)

    ret, stdout, stderr = run_subprocess(*args, shell=True, close_fds=True)
    if ret:
        raise ValueError("Error when running subprocess {}:\n {}\n{}".format(args, stdout, stderr))

    return pdf

def generate_pdf(urls, pdf, pdf_gen_name=None, **kwargs):
    pdf_gen_name = pdf_gen_name or settings.RISKS['PDF_GENERATOR']['NAME']
    pdf_gen = globals()['generate_pdf_{}'.format(pdf_gen_name)]

    return pdf_gen(urls, pdf)

