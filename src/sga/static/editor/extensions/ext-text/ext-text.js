const name = 'textcodes'

export default {
  name,
  async init ({ _importLocale }) {
    const svgEditor = this
    const { svgCanvas } = svgEditor
    const modeId = 'tool_textcodes'

    return {
           name: svgEditor.i18next.t(`${name}:name`),
           callback () {
            var classes=''
            var text_color=''
            const elements= document.querySelectorAll('.text_options')

            document.body.addEventListener('click',(e)=>{
              if (e.target.classList.contains('text_content')) {

              let content=e.target.textContent

              let target_id=e.target.id

              const curStyle = svgCanvas.getStyle()

              if(target_id==='Peligro'){
                text_color="#FF0000"
              }else{
                text_color="#000000"
              }
              classes = target_id
              const curShape = svgCanvas.addSVGElementsFromJson({
                  element: 'text',
                  curStyles: true,
                  attr: {
                    x:100,
                    y:100,
                    class:classes,
                    id: svgCanvas.getNextId(),
                    fill: svgCanvas.getCurText('fill'),
                    'stroke-width': svgCanvas.getCurText('stroke_width'),
                    'font-size': svgCanvas.getCurText('font_size'),
                    'font-family': svgCanvas.getCurText('font_family'),
                    'text-anchor': 'middle',
                    'xml:space': 'preserve',
                    opacity: curStyle.opacity
                  }
              })
               curShape.attributes.fill.value=text_color
               curShape.textContent=content

            svgCanvas.setSelectedElements(0, curShape)
            }
            })
        },
              mouseDown (opts) {
             // Check the mode on mouseup
             if (svgCanvas.getMode() === 'tool_textcodes') {
               const zoom = svgCanvas.getZoom()

               // Get the actual coordinate by dividing by the zoom value
               const x = opts.mouse_x / zoom
               const y = opts.mouse_y / zoom

               const text = svgEditor.i18next.t(`${name}:text`, { x, y })

             }
           },
        }
       }
     }
