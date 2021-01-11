class TextBoxTag():

    def __init__(self,props):
        self.properties = {
            'type': 'textbox',
            'originX': 'originX', 'originY': 'originY',
            'left': 'margin-left', 'top': 'margin-top',
            'width': 'width', 'height': 'height',
            'fill': 'color', 'stroke': 'stroke', 'color': 'color',
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
        self.wid = props["workarea"].width
        self.hei = props["workarea"].initial_height
        self.wa_scale_y = props["workarea"].pro_y

class ITextBoxTag():

    def __init__(self, props):
        self.properties = {
            'type': 'i-text',
            'originX': 'originX', 'originY': 'originY',
            'left': 'margin-left', 'top': 'margin-top',
            'width': 'width', 'height': 'height',
            'fill': 'color', 'stroke': 'stroke', 'color': 'color',
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
        self.wid = props["workarea"].width
        self.hei = props["workarea"].initial_height
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y

class ImageTag():

    def __init__(self,props):
        self.properties = {
            'type': 'image',
            'originX': 'originX', 'originY': 'originY',
            'left': 'margin-left', 'top': 'margin-top',
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
        self.wid = props["workarea"].width
        self.hei = props["workarea"].initial_height
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
            'angle': 'angle','fontSize': 'font-size',
            'opacity': 'opacity', 'shadow': 'shadow', 'visible': 'visible',
            'clipTo': 'clip', 'backgroundColor': 'background-color',
            'fillRule': 'fill-rule', 'paintFirst': 'first-paint',
            'skewX': 'skewX', 'skewY': 'skewY', 'x1': 'x1', 'x2': 'x2', 'y1': 'y1', 'y2': 'y2'
        }
        self.json_props = props["json_data"]
        self.wid = props["workarea"].width
        self.hei = props["workarea"].initial_height
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y


class TagStyleParser(TextBoxTag,ImageTag,LineTag,ITextBoxTag):

    styles = "position:absolute; padding:0;"
    tag = ""
    cm = 0.0264583333
    warningword = ['Peligro']

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
            self.tag = "<p style=\"%s\">%s</p>" % (self.parse_data(), self.convert_danger(self.json_props['text']))
            #print(self.tag)
        if (self.type == "image"):
            self.tag = "<img style=\"%s\" src=\"%s\">" % (self.parse_data(), self.json_props['src'])
            #print(self.tag)
        if (self.type == "i-text"):
            self.tag = "<p style=\"%s\">%s</p>" % (self.parse_data(), self.json_props['text'])
        if (self.type == "line"):
            self.tag = "<hr style=\"%s;%s\">" % (self.parse_data(), self.get_hr_specific_styles())
        return self.tag

    def get_hr_specific_styles(self):
        css = ""
        css += "border-color: %s;" % self.json_props["stroke"]
        return css

    def pop_from_dict(self, items):
        for key in items:
            self.properties.pop(key)

    def parse_data(self):

        if self.json_props['scaleX'] and self.json_props['scaleY']:
            if 'src' in self.json_props:
                grades=int(float(self.json_props['angle']))
                if self.json_props['angle'] > 2:
                    self.styles += "transform: scale({},{}) rotate({});".format(
                    self.json_props['scaleY'],self.json_props['scaleX'],
                    str(grades)+"deg")

                else:
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])

            else:
                width = self.json_props["width"] * self.cm
                left = self.json_props['left'] * self.cm


                if (width+left)*2>=self.wid:
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])
                    self.styles += "{}:{};".format("font-size", self.conversion_fontsize())
                else:
                    if 'text' in self.json_props:
                        self.styles += "{}:{};".format("font-size", self.conversion_fontsize())
                        if self.json_props['text'] in self.warningword:
                            self.styles += "{}:{};".format('color', 'red')
                    self.styles += "{}:{};".format('width', self.conversion_width('width', self.json_props) + 'cm')
                    self.styles += "{}:{};".format('height', self.conversion_height('height') + 'cm')

        if self.json_props['originX'] and self.json_props['originY']:
            self.styles += f"transform-origin: {self.json_props['originX']} {self.json_props['originY']};"


        if self.json_props['backgroundColor']=='':
            self.styles += "{}:{};".format('background-color', 'white')

        top_value = str((self.json_props['top']) * self.cm) + 'cm'
        left_value = str((self.json_props['left']) * self.cm) + 'cm'
        self.styles += "{}:{};".format('top', top_value)
        self.styles += "{}:{};".format('left', left_value)

        return self.styles

    def conversion_width(self, key, src):
        sizes = str(self.json_props[key]*self.cm)
        sizes = str(sizes)

        return sizes
    def conversion_height(self, key):
        sizes = str(self.json_props[key]*self.cm)
        return sizes

    def conversion_fontsize(self):
        return str((int(float(self.json_props['fontSize'])))*self.cm) + 'cm'

    def convert_danger(self,text):
        i = 0
        x = 6
        result=""
        while i < len(text):
            if text[i:x] == "Danger":
                result +="<br><br><strong>Danger </strong>"
                i = x
                x += 6
            else:
                result += text[i]
                i += 1
                x += 1
        return result