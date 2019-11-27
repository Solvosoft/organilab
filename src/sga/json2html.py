import json
from xhtml2pdf.util import getSize


class WorkArea:
    def __init__(self, width, height):
        self.ref_left = 0  # pixel length
        self.ref_top = 0
        self.ref_width = 0
        self.ref_height = 0

        self.inital_width = getSize(width)
        self.inital_height = getSize(height)

    def set_reference_instance(self, width, height, top=0, left=0):
        self.ref_left=getSize("%.2fpx"%(left))  # pixel length
        self.ref_top=getSize("%.2fpx"%(top))
        self.ref_width = getSize("%.2fpx"%(width))
        self.ref_height = getSize("%.2fpx"%(height))

        self.prop_y = (100*self.ref_height)/self.inital_height
        self.prop_x = (100*self.ref_width)/self.inital_width

    def convert_to_units(self, value):
        return getSize("%.2fpx"%(value))

    def get_position(self, data):
        left=getSize("%.2fpx"%(data['left'])) # pixel length
        top=getSize("%.2fpx"%(data['top']))
        width = getSize("%.2fpx"%(data['width']))
        height = getSize("%.2fpx"%(data['height']))
        left = (left-self.ref_left)*self.prop_x
        top = (top - self.ref_top)*self.prop_y
        width = (width - self.ref_width)*self.prop_x
        height = (height - self.ref_height)*self.prop_y

        return (left, top, width, height)


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
    return "<!DOCTYPE html><html><head><style>"


# add background color that already define in json
def add_background(color):
    return "body{background-color:%s;}" % color


# Setting page size with Css to render to pdf size, @media print is other way to render size properly in Css
def ending_of_styles(info_recipient):
    ending_tags = '</style></head><body>'
    page_size = str(info_recipient['height_value']) + info_recipient['height_unit'] + ' ' + str(
        info_recipient['width_value']) + info_recipient['width_unit']
    height = str(info_recipient['height_value']) + info_recipient['height_unit']
    width = str(info_recipient['width_value']) + info_recipient['width_unit']
    margin = "1mm"
    ending_tags = "@page {size: %s;margin: %s;} @media print{body{ width: %s; height: %s;margin:%s;}} %s" % (
        page_size, margin, height, width, margin, ending_tags)
    return ending_tags


# Convert Json elements inside html
def render_body(json_elements, workarea):
    body_data = ""
    for elem in json_elements:
        if elem["type"] == "i-text" or elem["type"] == "textbox":
            tag = "<p style=\"%s\">%s</p>" % (get_styles(elem, workarea), elem["text"])
            body_data += tag
        elif elem["type"] == "image":
            tag = "<img style=\"%s\" src=\"%s\">" % (get_styles(elem, workarea), elem["src"])
            body_data += tag
        elif elem["type"] == "line":
            tag = "<hr style=\"%s;%s\">" % (get_styles(elem, workarea), get_hr_specific_styles(elem))
            body_data += tag
    return body_data


# Add border color that already define in json
def get_hr_specific_styles(json_data):
    css = ""
    css += "border-color: %s;" % json_data["stroke"]
    return css


# Define position and Style of the elements in html
def get_styles(json_data, workarea):
    styles = "position:absolute;"
    available_css_mappings = ("left", "top", "width", "height", "fill")
    unformatted_mappings = (
        "fontSize", "fontFamily", "fontWeight", "fontStyle", "textAlign", "lineHeight", "strokeWidth")

    if "scaleX" in json_data:
        styles += "transform: scaleX({}) scaleY({});".format(json_data["scaleX"], json_data["scaleY"])

    positions = workarea.get_position(json_data)
    styles += "left: %0.3f; top: %0.3f; width: %0.3f; height: %0.3f"%(positions)
    for elem in json_data:
        if elem in unformatted_mappings:
            css_key = format_to_css(elem)
            css_value = str(json_data[elem])
            css_value += append_unit(css_key)
            styles += "{}:{};".format(css_key, css_value)
    return styles


def format_to_css(string):
    formatted = string
    for i, letter in enumerate(string):
        if letter.isupper():
            formatted = string[:i] + "-" + string[i:]
    return formatted.lower()


# Define size in px in html
def append_unit(string):
    unit = ""
    append_px = ("left", "top", "width", "height")
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
