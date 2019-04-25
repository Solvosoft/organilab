import json


def json2html(json_data):
    if type(json_data) == str:
        html_data = beginning_of_html()
        parsed_json = json.loads(json_data)
        html_data += add_background(color=parsed_json["background"])
        for i, elem in enumerate(parsed_json):
            if elem == "objects":
                html_data += ending_of_styles()
                html_data += render_body(parsed_json[elem])
        html_data += ending_of_html()
        print(html_data)
        return html_data
    else:
        raise ValueError("The parameter json_data should be a string encoded json")


def render_body(json_elements):
    body_data = ""
    for elem in json_elements:
        if elem["type"] == "i-text" or elem["type"] == "textbox":
            tag = "<p style=\"%s\">%s</p>" % (get_styles(elem), elem["text"])
            body_data += tag
        elif elem["type"] == "image":
            tag = "<img style=\"%s\" src=\"%s\">" % (get_styles(elem), elem["src"])
            body_data += tag
        elif elem["type"] == "line":
            tag = "<hr style=\"%s;%s\">" % (get_styles(elem), get_hr_specific_styles(elem))
            body_data += tag
    return body_data


def get_hr_specific_styles(json_data):
    css = ""
    css += "border-color: %s;" % json_data["stroke"]
    return css


def get_styles(json_data):
    styles = "position:absolute;"
    available_css_mappings = ("left", "top", "width", "height", "fill")
    unformatted_mappings = ("fontSize", "fontFamily", "fontWeight", "textAlign")
    if "scaleX" in json_data:
        styles += "transform: scaleX({}) scaleY({});".format(json_data["scaleX"], json_data["scaleY"])
    for elem in json_data:
        if elem in available_css_mappings:
            css_key = elem
            css_value = str(json_data[elem]) + append_unit(elem)
            styles += "{}:{};".format(css_key, css_value)
        elif elem in unformatted_mappings:
            css_key = format_to_css(elem)
            css_value = json_data[elem]
            css_value += append_unit(css_key)
            styles += "{}:{};".format(css_key, css_value)
    return styles


def format_to_css(string):
    formatted = string
    for i, letter in enumerate(string):
        if letter.isupper():
            formatted = string[:i] + "-" + string[i:]
    return formatted.lower()


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


def add_background(color):
    return "body{background-color:%s;}" % color


def beginning_of_html():
    return "<!DOCTYPE html><html><head><style>"


def ending_of_html():
    return "</body></html>"


def ending_of_styles():
    return "</style></head><body>"
