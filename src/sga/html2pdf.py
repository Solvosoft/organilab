from pdf2image import convert_from_path

from django.http import HttpResponseNotFound
from django.core.files import temp as tempfile

def pdf2tiff(pdf_path):
    """
           Parameters:
               pdf_path -> Path to the PDF that you want to convert
               dpi -> Image quality in DPI (default 200)
               output_folder -> Write the resulting images to a folder (instead of directly in memory)
               first_page -> First page to process
               last_page -> Last page to process before stopping
               fmt -> Output image format
               thread_count -> How many threads we are allowed to spawn for processing
               userpw -> PDF's password
               use_cropbox -> Use cropbox instead of mediabox
               strict -> When a Syntax Error is thrown, it will be raised as an Exception
               transparent -> Output with a transparent background instead of a white one.
               single_file -> Uses the -singlefile option from pdftoppm/pdftocairo
               output_file -> What is the output filename or generator
               poppler_path -> Path to look for poppler binaries
               grayscale -> Output grayscale image(s)
               size -> Size of the resulting image(s), uses the Pillow (width, height) standard
               paths_only -> Don't load image(s), return paths instead (requires output_folder)
    """
    output_file = tempfile.gettempdir() + "/resultiff.tiff"  # path final tiff
    format = "tiff"
    try:
        convert_from_path(pdf_path=pdf_path, fmt=format, output_file=output_file)
    except IOError:
        return HttpResponseNotFound()
    return output_file