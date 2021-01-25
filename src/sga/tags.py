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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height
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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height
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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height
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
        self.width = props["workarea"].initial_width
        self.height = props["workarea"].initial_height
        self.wa_scale_x = props["workarea"].pro_x
        self.wa_scale_y = props["workarea"].pro_y


class TagStyleParser(TextBoxTag,ImageTag,LineTag,ITextBoxTag):

    styles = "position:absolute; padding:0;line-height: 1em;"
    tag = ""
    cm = 0.0264583333
    warningword = ['Peligro','peligro','Atención','atención']

    def __init__(self, props):
        self.to_append_px = ("font-size", "width", "height")
        self.type = props['type']
        self.template_width = int(float(props['sizes'].width))
        self.template_height = int(float(props['sizes'].height))
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
            self.tag = "<p style=\"%s\">%s</p>" % (self.parse_data(), self.separate_title(self.convert_header(self.json_props['text'])))
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
        width = self.convertion()
        height = self.conversion_h()
        top_value = str(self.getY(height)) + 'cm'
        left_value = str(self.getX(width)) + 'cm'
        self.styles += "{}:{};".format('top', top_value)
        self.styles += "{}:{};".format('left', left_value)
        if self.json_props['scaleX'] and self.json_props['scaleY']:
            if 'src' in self.json_props:
                grades=int(float(self.json_props['angle']))

                if self.json_props['angle'] > 2:
                    self.styles += "transform: scale({},{}) rotate({});".format(
                    self.json_props['scaleY']*height,self.json_props['scaleX']*width,
                    str(grades)+"deg")

                else:
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX']*width,
                        self.json_props['scaleY']*height)

            else:
                extra_width = self.json_props["width"] * self.cm*self.convertion()
                left = self.json_props['left'] * self.cm*width

                font= self.conversion_fontsize()
                if (extra_width+left) >= self.width:
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])

                elif self.type=='i-text':
                    self.styles += "transform: scale({},{});".format(
                        self.json_props['scaleX'],
                        self.json_props['scaleY'])
                    print("{}----------{}-------{}".format(self.json_props['text'], 0.7672916657000001>0.108214583197,self.getY(height)))
                else:

                    self.styles += "{}:{};".format('width', str(self.conversion_width()) + 'cm')
                    self.styles += "{}:{};".format('height', str(self.conversion_height()) + 'cm')

                if 'text' in self.json_props:
                    if self.json_props['text'] in self.warningword:
                        self.styles += "{}:{};".format('color', 'red')
                self.styles += "{}:{};".format("font-size", font)

        if self.json_props['originX'] and self.json_props['originY']:
            self.styles += f"transform-origin: {self.json_props['originX']} {self.json_props['originY']};"

        if self.json_props['backgroundColor'] == '':
            self.styles += "{}:{};".format('background-color', 'white')

        return self.styles

    def conversion_width(self):
        sizes = (self.json_props['width']*self.cm)*self.convertion()
        return sizes

    def conversion_height(self):
        sizes = (self.json_props['height']*self.cm)*self.conversion_h()
        return sizes

    def conversion_fontsize(self):
         convertX = self.conversion_width()
         convertY = self.conversion_height()
         aux = float(self.json_props['fontSize'])*self.cm
         x = (float(aux/convertX))
         y = float((aux*convertY))
         z = aux*self.conversion_h()
         #print(z)
         if x >= y:
            z = aux*self.convertion()
         #print(z)
         return str((aux*self.convertion()+aux*self.conversion_h())*0.5) + 'cm'

    def convert_header(self,text):
        data = text
        if text.find('Consejos de Prudencia')>-1:
            data = "<strong>Consejos de Prudencia</strong><br>"
            data += text[len('Consejos de Prudencia'):len(text)]
        if text.find('Indicaciones de Peligro')>-1:
            data = "<strong>Indicaciones de Peligro</strong><br>"
            data += text[len('Indicaciones de Peligro'):len(text)]
        return data


    def validate_concat(self,text, i,j):
        position = j
        while i < len(text):
            if text[j+2] == '+':
                j += 7
                position = j
            else:
                break
        return position

    def separate_title(self,text):
        i = 0
        output = ""
        x = 3
        while i<len(text):

            if (text[i] == 'H' and str(text[i+1:x]).isnumeric()) or (text[i]=='P' and str(text[i+1:x]).isnumeric()):
                j = self.validate_concat(text,i,x)
                output += '<br>'+text[i:j]
                i = j
                x = i+3
            else:
                output += text[i]
                x += 1
                i += 1

        return output

    def getY(self, height):
        result = abs((self.json_props['top']*self.cm)/height)
        print('{}ddd'.format(result))
        if self.template_height > self.height:
            result = (self.json_props['top']*self.cm)*height
            print(result)

        return abs(result)

    def getX(self, width):

        result = (self.json_props['left'] * self.cm) / width

        if self.template_width > self.width:
            result = (self.json_props['left'] * self.cm) * width

        return result

    def convertion(self):
        result = self.template_width/self.width
        if self.template_width > self.width:
            result = self.width/self.template_width
        return result

    def conversion_h(self):

        result = self.template_height/self.height

        if self.template_height > self.height:
            result = self.height/self.template_height

        return result