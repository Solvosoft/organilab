import json

from xhtml2pdf.util import getSize

from sga.json2html_styleparser import TagStyleParser


class WorkArea:
    def __init__(self, width, height):
        self.ref_left = 0
        self.ref_top = 0
        self.ref_width = 0
        self.ref_height = 0
        self.pro_y = 0
        self.pro_x = 0
        self.initial_width = getSize(width)
        self.initial_height = getSize(height)
        self.width = int(float(width[0:-2]))

    def set_reference_instance(self, width, height, top=0, left=0):
        self.ref_left = getSize("%.2fpx" % left)
        self.ref_top = getSize("%.2fpx" % top)
        self.ref_width = getSize("%.2fpx" % width)
        self.ref_height = getSize("%.2fpx" % height)
        self.pro_y = self.ref_height / self.initial_height
        self.pro_x = self.ref_width / self.initial_width

# Prepare and convert json objects into python objects
def json2html(json_data, info_recipient):
    if type(json_data) == str:
        html_data = beginning_of_html()
        parsed_json = json.loads(json_data)
        html_data += add_background(color=parsed_json["background"])
        html_data += ending_of_styles(info_recipient)
        workarea = WorkArea(
            width="%.2f%s" % (info_recipient['width_value'], info_recipient['width_unit']),
            height="%.2f%s" % (info_recipient['height_value'], info_recipient['height_unit']),
        )
        if 'objects' in parsed_json:
            dataobjs = iter(parsed_json['objects'])
            base = next(dataobjs)
            workarea.set_reference_instance(
                base['width'], base['height'], base['top'], base['left']
            )
            html_data += render_body(dataobjs, workarea)

        html_data += ending_of_html()
        return html_data

    else:
        raise ValueError("The parameter json_data should be a string encoded json")


# Define First tags of html
def beginning_of_html():
    return "<html><style type=\"%s\">" % "text/css"


# add background color that already define in json
def add_background(color):
    return "body{background-color:white; padding:0; margin:0; position:relative;}"


# Setting page size with Css to render to pdf size, @media print is other way to render size properly in Css
def ending_of_styles(info_recipient):
    ending_tags = '</style><body>'
    height = str(int(info_recipient['height_value'])) + info_recipient['height_unit']
    width = str(int(info_recipient['width_value'])) + info_recipient['width_unit']
    page_size = height + ' ' + width
    print(page_size)
    margin = "1mm"
    #body stretch is needed because we don't have the image scalated.
    #You can take away the body stretch if you have properly size to the image you want to render
    #Is a better solution not use body stretch, and keep the flow in different pages
    ending_tag = "@page {height:%s; width:%s; padding:0; margin:0; size: A4;}  %s" % (height, width, ending_tags)
    return ending_tag


# Convert Json elements inside html
def render_body(json_elements, work_area):
    body_data = ""
    #header='<div id="header_content"><table width="100%"><tr><td style="text-align:left;">verbose title</td><td style="text-align:right;">Date here</td></tr></table></div>'
    for elem in json_elements:
        if 'text' in elem:
            if len(elem['text']) > 0:
                style_parser = TagStyleParser({'type':elem['type'],'json_data':elem,'workarea':work_area})
                body_data += style_parser.set_tag()
             #   print(style_parser.set_tag())
        else:
            style_parser = TagStyleParser({'type': elem['type'], 'json_data': elem, 'workarea': work_area})
            body_data += style_parser.set_tag()
            #print(style_parser.set_tag())

    return body_data


    #print(body_data)
    #footer = '</div><div id="footer_content"><table width="100%"><tr><td style="text-align:left;">user here</td><td style="text-align:right;"><pdf:pagenumber> of <pdf:pagecount></td></tr></table></div>'
    #body_data += footer

# Sort the JSON elements by Margin-Top

def order_elements(json_elements):
    datalist = []
    for elem in json_elements:
        datalist.append(elem)

    for element in range(len(datalist) - 1, 0, -1):
        for i in range(element):
            if datalist[i]['top'] > datalist[i + 1]['top']:
                temp = datalist[i]
                datalist[i] = datalist[i + 1]
                datalist[i + 1] = temp

    return datalist
#TODO check if we need this change  from px to em
# Define size in px in html
def append_unit(string):
    unit = ""
    append_px = ("left", "top", "width", "height", "min-width")
    append_em = ("font-size",)
    if string in append_px:
        unit = "px"
    elif string in append_em:
        # TODO change to em when proportions are ready
        unit = "px"
    return unit


# Ending tags of html
def ending_of_html():
    return "</body></html>"