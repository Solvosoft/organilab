'''
Created on 30 jun. 2018

@author: luis
'''
from django import template
from django.utils.safestring import mark_safe
from django.conf import settings
register = template.Library()
import os


PDFJS = """
<script>
var pdfurl = '%(pdfurl)s';


// Loaded via <script> tag, create shortcut to access PDF.js exports.
var pdfjsLib = window['pdfjs-dist/build/pdf'];

// The workerSrc property shall be specified.
pdfjsLib.GlobalWorkerOptions.workerSrc = '//mozilla.github.io/pdf.js/build/pdf.worker.js';

var pdfDoc = null,
    pageNum = 1,
    pageRendering = false,
    pageNumPending = null,
    scale = 1.2,
    canvas = document.getElementById('%(canvas)s'),
    ctx = canvas.getContext('2d');

/**
 * Get page info from document, resize canvas accordingly, and render page.
 * @param num Page number.
 */
function renderPage(num) {
  pageRendering = true;
  // Using promise to fetch the page
  pdfDoc.getPage(num).then(function(page) {
    var viewport = page.getViewport(scale);
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    // Render PDF page into canvas context
    var renderContext = {
      canvasContext: ctx,
      viewport: viewport
    };
    var renderTask = page.render(renderContext);

    // Wait for rendering to finish
    renderTask.promise.then(function() {
      pageRendering = false;
      if (pageNumPending !== null) {
        // New page rendering is pending
        renderPage(pageNumPending);
        pageNumPending = null;
      }
    });
  });

  // Update page counters
  document.getElementById('page_num').textContent = num;
}

/**
 * If another page rendering in progress, waits until the rendering is
 * finised. Otherwise, executes rendering immediately.
 */
function queueRenderPage(num) {
  if (pageRendering) {
    pageNumPending = num;
  } else {
    renderPage(num);
  }
}

/**
 * Displays previous page.
 */
function onPrevPage() {
  if (pageNum <= 1) {
    return;
  }
  pageNum--;
  queueRenderPage(pageNum);
}
document.getElementById('prev').addEventListener('click', onPrevPage);

/**
 * Displays next page.
 */
function onNextPage() {
  if (pageNum >= pdfDoc.numPages) {
    return;
  }
  pageNum++;
  queueRenderPage(pageNum);
}
document.getElementById('next').addEventListener('click', onNextPage);

/**
 * Asynchronously downloads PDF.
 */
pdfjsLib.getDocument(pdfurl).then(function(pdfDoc_) {
  pdfDoc = pdfDoc_;
  document.getElementById('page_count').textContent = pdfDoc.numPages;

  // Initial/first page rendering
  renderPage(pageNum);
});
</script>
"""


def get_object_name(name):
    dev = name
    if len(name) > 5:
        dev = str(name[-5:])
    return dev.replace('/', '')


@register.simple_tag(takes_context=True)
def is_pdf_object(context, name):
    ext = os.path.splitext(name)
    ext = ext[1].lower()
    return ext == '.pdf'


@register.simple_tag(takes_context=True)
def get_pdf_viewjs(context, name):
    ext = os.path.splitext(name)
    filename = get_object_name(ext[0])
    ext = ext[1].lower()

    if ext == '.pdf':
        return mark_safe(PDFJS % {
            'pdfurl': "%s%s" % (settings.STATIC_URL, name),
            'canvas': filename
        })

    return ''


@register.simple_tag(takes_context=True)
def get_pdf_viewcanvas(context, name):
    ext = os.path.splitext(name)
    filename = get_object_name(ext[0])
    ext = ext[1].lower()
    if ext == '.pdf':
        return mark_safe("""<canvas id="%s"></canvas>""" % (filename,))

    return ''
