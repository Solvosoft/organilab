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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height

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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height

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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height

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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height


class TagStyleParser(TextBoxTag,ImageTag,LineTag,ITextBoxTag):

    styles = "position:absolute; padding:0;"
    tag = ""
    warningword = ['Peligro','peligro','Atención','atención']

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
            self.tag = "<p style=\"%s\">%s</p>" % (self.parse_data(), self.convert_header(self.json_props['text']))
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

    def pop_from_dict(self, items):
        for key in items:
            self.properties.pop(key)

    def parse_data(self):
        self.styles += "{}:{};".format('top', str(self.json_props['top'])+'px')
        self.styles += "{}:{};".format('left', str(self.json_props['left'])+'px')


        if self.json_props['scaleX'] and self.json_props['scaleY']:
            if 'src' in self.json_props:
                grades=int(float(self.json_props['angle']))

                if self.json_props['angle'] > 2:
                    self.styles += "transform: scale({},{}) rotate({});".format(
                    self.json_props['scaleY'],self.json_props['scaleX'],
                    str(grades)+"deg")

                else:
                    self.styles += self.convertion_scale()

            else:

                extra_width = int(float(self.json_props["width"]))
                left = self.json_props['left']

                if (extra_width+left) >= self.width:
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])

                elif self.type=='i-text':
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])
                else:
                    self.styles += "{}:{};".format('width', str( (self.json_props['width']*self.json_props['scaleX'])) + 'px')
                    self.styles += "{}:{};".format('height', str(self.json_props['height']*self.json_props['scaleY']) + 'px')
                if 'text' in self.json_props:

                        self.styles += "{}:{};".format('color', self.json_props['fill'])
                        self.styles += "{}:{};".format('text-align', self.json_props['textAlign'])
                self.styles += "{}:{};".format("font-size", str(float(self.json_props['fontSize']))+'px')
                self.styles += "line-height:{};".format(self.json_props['lineHeight'])

        if self.json_props['originX'] and self.json_props['originY']:
            self.styles += f"transform-origin: {self.json_props['originX']} {self.json_props['originY']};"
        if self.json_props['backgroundColor'] == '':
            self.styles += "{}:{};".format('background-color', 'transparent')
        else:
            self.styles += "{}:{};".format('background-color', self.json_props['backgroundColor'])

        return self.styles


    def convert_header(self,text):
        data = text
        if text.find('Consejos de Prudencia')>-1:
            data = "<strong>Consejos de Prudencia</strong><br>"
            data += text[len('Consejos de Prudencia'):len(text)]
        if text.find('Indicaciones de Peligro')>-1:
            data = "<strong>Indicaciones de Peligro</strong><br>"
            data += text[len('Indicaciones de Peligro'):len(text)]
        return data


    def convertion_scale(self):
        result= "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])

        return result;