class TextBoxTag():

    def __init__(self,props):
        self.properties = {
            'type': 'textbox',
            'originX': 'originX', 'originY': 'originY',
            'left': 'left', 'top': 'top',
            'width': 'width', 'height': 'height',
            'fill': 'color', 'stroke': 'stroke',
            'strokeWidth': 'stroke-width', 'strokeDashArray': 'stroke-dasharray',
            'strokeLineCap': 'stroke-linecap', 'strokeLineJoin': 'stroke-linejoin',
            'strokeMiterLimit': 'stroke-miterlimit',
            'scaleX': 'scaleX', 'scaleY': 'scaleY',
            'angle': 'angle',
            'opacity': 'opacity', 'shadow': 'shadow', 'visible': 'visible',
            'clipTo': 'clip', 'backgroundColor': 'background-color',
            'fillRule': 'fill-rule', 'paintFirst': 'first-paint',
            'skewX': 'skewX', 'skewY': 'skewY', 'text': 'text',
            'fontSize': 'font-size', 'fontWeight': 'font-weight',
            'fontFamily': 'font-family', 'fontStyle': 'font-style',
            'lineHeight': 'line-height', 'underline': 'underline', 'overline': 'overline',
            'linethrough': 'linethrough', 'textAlign': 'text-align',
            'charSpacing': 'letter-spaclefting', 'minWidth': 'min-width', 'styles': {}
        }
        self.json_props = props["json_data"]
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y

class ITextBoxTag():

    def __init__(self, props):
        self.properties = {
            'type': 'i-text',
            'originX': 'originX', 'originY': 'originY',
            'left': 'left', 'top': 'top',
            'width': 'width', 'height': 'height',
            'fill': 'color', 'stroke': 'stroke',
            'strokeWidth': 'stroke-width', 'strokeDashArray': 'stroke-dasharray',
            'strokeLineCap': 'stroke-linecap', 'strokeLineJoin': 'stroke-linejoin',
            'strokeMiterLimit': 'stroke-miterlimit',
            'scaleX': 'scaleX', 'scaleY': 'scaleY',
            'angle': 'angle',
            'opacity': 'opacity', 'shadow': 'shadow', 'visible': 'visible',
            'clipTo': 'clip', 'backgroundColor': 'background-color',
            'fillRule': 'fill-rule', 'paintFirst': 'first-paint',
            'skewX': 'skewX', 'skewY': 'skewY', 'text': 'text',
            'fontSize': 'font-size', 'fontWeight': 'font-weight',
            'fontFamily': 'font-family', 'fontStyle': 'font-style',
            'lineHeight': 'line-height', 'underline': 'underline', 'overline': 'overline',
            'linethrough': 'linethrough', 'textAlign': 'text-align',
            'charSpacing': 'letter-spaclefting', 'styles': {}
        }
        self.json_props = props["json_data"]
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y

class ImageTag():

    def __init__(self,props):
        self.properties = {
            'type': 'image',
            'originX': 'originX', 'originY': 'originY',
            'left': 'left', 'top': 'top',
            'width': 'width', 'height': 'height',
            'fill': 'color', 'stroke': 'stroke',
            'strokeWidth': 'stroke-width', 'strokeDashArray': 'stroke-dasharray',
            'strokeLineCap': 'stroke-linecap', 'strokeLineJoin': 'stroke-linejoin',
            'strokeMiterLimit': 'stroke-miterlimit',
            'scaleX': 'scaleX', 'scaleY': 'scaleY',
            'angle': 'angle',
            'opacity': 'opacity', 'shadow': 'shadow', 'visible': 'visible',
            'clipTo': 'clip', 'backgroundColor': 'background-color',
            'fillRule': 'fill-rule', 'paintFirst': 'first-paint',
            'skewX': 'skewX', 'skewY': 'skewY', 'crossOrigin': 'crossorigin', 'src': 'src', 'filters': {}
        }
        self.json_props = props["json_data"]
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y

class LineTag():

    def __init__(self,props):
        self.properties = {
            'type': 'line',
            'originX':'originX','originY': 'originY',
            'left': 'left', 'top': 'top',
            'width': 'width', 'height': 'height',
            'fill': 'color', 'stroke': 'stroke',
            'strokeWidth': 'stroke-width', 'strokeDashArray': 'stroke-dasharray',
            'strokeLineCap': 'stroke-linecap', 'strokeLineJoin': 'stroke-linejoin',
            'strokeMiterLimit': 'stroke-miterlimit',
            'scaleX': 'scaleX', 'scaleY': 'scaleY',
            'angle': 'angle',
            'opacity': 'opacity', 'shadow': 'shadow', 'visible': 'visible',
            'clipTo': 'clip', 'backgroundColor': 'background-color',
            'fillRule': 'fill-rule', 'paintFirst': 'first-paint',
            'skewX': 'skewX', 'skewY': 'skewY', 'x1': 'x1', 'x2': 'x2', 'y1': 'y1', 'y2': 'y2'
        }
        self.json_props = props["json_data"]
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y


class TagStyleParser(TextBoxTag,ImageTag,LineTag,ITextBoxTag):

    styles = "position:absolute;"
    tag = ""
    def __init__(self, props):
        self.to_append_px = ("font-size", "width", "height")
        self.type = props['type']
        if(self.type == "textbox"):
            TextBoxTag.__init__(self, props)
        if(self.type == "image"):
            ImageTag.__init__(self, props)
        if(self.type == "i-text"):
            ITextBoxTag.__init__(self, props)
        if(self.type == "line"):
            LineTag.__init__(self, props)
    def set_tag(self):
        if (self.type == "textbox"):
            self.tag = "<p style=\"%s\">%s</p>" % (self.parse_data(), self.json_props['text'])
        if (self.type == "image"):
            self.tag = "<img style=\"%s\" src=\"%s\">" % (self.parse_data(), self.json_props['src'])
        if (self.type == "i-text"):
            self.tag = "<p style=\"%s\">%s</p>" % (self.parse_data(), self.json_props['text'])
        if (self.type == "line"):
            self.tag = "<hr style=\"%s;%s\">" % (self.parse_data(), self.get_hr_specific_styles())
        return self.tag

    def get_hr_specific_styles(self):
        css = ""
        css += "border-color: %s;" % self.json_props["stroke"]
        return css
    def pop_from_dict(self,items):
        for key in items:
            self.properties.pop(key)

    def parse_data(self):
        if self.json_props['scaleX'] and self.json_props['scaleY']:
            self.styles += "transform: scale({},{});".format(
                self.json_props['scaleX'] / self.wa_scale_x,
                self.json_props['scaleY'] / self.wa_scale_y)
            self.pop_from_dict(['scaleY', 'scaleX'])
        if self.json_props['originX'] and self.json_props['originY']:
            self.styles += f"transform-origin: {self.json_props['originX']} {self.json_props['originY']};"
            self.pop_from_dict(['originY', 'originX'])
        if self.json_props['top'] and self.json_props['left']:
            top_value = str(self.json_props['top'] / self.wa_scale_y) + 'px'
            left_value = str(self.json_props['left'] / self.wa_scale_y) + 'px'
            self.styles += "{}:{};".format('top', top_value)
            self.styles += "{}:{};".format('left', left_value)
            self.pop_from_dict(['top', 'left'])
        for key, value in self.properties.items():
            if self.json_props[key]:
                self.styles += "{}:{};".format(value, self.json_props[key] if key not in self.to_append_px else
                str(self.json_props[key]) + 'px')
        return self.styles


