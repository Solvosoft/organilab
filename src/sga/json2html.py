import json


# Prepare and convert json objects into python objects
def json2html(json_data, info_recipient, label_info_recipient):
    if type(json_data) == str:
        html_data = beginning_of_html()
        parsed_json = json.loads(json_data)
        html_data += add_background(color=parsed_json["background"])
        for i, elem in enumerate(parsed_json):
            if elem == "objects":
                html_data += ending_of_styles(info_recipient)
                html_data += render_body(parsed_json[elem], info_recipient, label_info_recipient)
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
def render_body(json_elements, info_recipient, label_info_recipient):
    body_data = ""
    for elem in json_elements:
        if elem["type"] == "i-text" or elem["type"] == "textbox":
            tag = "<p style=\"%s\">%s</p>" % (get_styles(elem, info_recipient, label_info_recipient, "t"), elem["text"])
            body_data += tag
        elif elem["type"] == "image":
            tag = "<img style=\"%s\" src=\"%s\">" % (get_styles(elem, info_recipient, label_info_recipient, "i"), elem["src"])
            body_data += tag
        elif elem["type"] == "line":
            tag = "<hr style=\"%s;%s\">" % (get_styles(elem, info_recipient, label_info_recipient, "l"), get_hr_specific_styles(elem))
            body_data += tag

    return body_data


# Add border color that already define in json
def get_hr_specific_styles(json_data):
    css = ""
    css += "border-color: %s;" % json_data["stroke"]
    return css


# Define position and Style of the elements in html
def get_styles(json_data, info_recipient, label_info_recipient, type):
    styles = "position:absolute;"
    available_css_mappings = ("width", "height", "fill")
    height_label = label_info_recipient["height_value"]
    width_label = label_info_recipient["width_value"]
    scaleX = info_recipient["width_value"] / width_label
    scaleY = info_recipient["height_value"] / height_label ##value for the proportion, 12 must be the initial template size
    all_types = {"t":0,"i":-300,"l":0}
    int_to_ubic = all_types[type]
    if "scaleX" in json_data:
            styles += "transform: scaleX({}) scaleY({});".format(json_data["scaleX"] * scaleX , json_data["scaleY"] * scaleY)
    for elem in json_data:
        if "scaleX" in json_data:
            pass
        css_key = elem
        if elem == "left":
            css_value = str(int_to_ubic + json_data[elem] * scaleX) + append_unit(
                elem)
        elif elem == "top":
            css_value = str(int_to_ubic + json_data[elem] * scaleY) + append_unit(
                elem)
        else:
            css_value = str(json_data[elem])
            if not elem in available_css_mappings:
                css_key = format_to_css(elem)
                css_value += append_unit(css_key)
            else:
                css_value += append_unit(elem)
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
