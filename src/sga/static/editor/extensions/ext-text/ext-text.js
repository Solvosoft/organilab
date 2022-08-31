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

            const elements= document.querySelectorAll('.text_options')
    
            document.body.addEventListener('click',(e)=>{
              if (e.target.classList.contains('text_content')) {

              let content=e.target.textContent

              let target_id=e.target.id

              const curStyle = svgCanvas.getStyle()  
              const curShape = svgCanvas.addSVGElementsFromJson({
                  element: 'text',
                  curStyles: true,
                  attr: {
                    x:100,
                    y:100,
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
              if(target_id==='dangerindication' || target_id==='warningword' || 
              target_id ==='prudenceword'){
                curShape.textContent = `{{${target_id}}}`
                curShape.attributes.fill.value="#FF0000"
              }else if(target_id==='uipa' || target_id ==='casname' 
              || target_id === "substancename" || target_id === "selername"
              || target_id ==="seleraddress" || target_id === "commercialinformation"){
                curShape.textContent=`{{${target_id}}}`
                curShape.attributes.fill.value="#000000"
              }else{
                curShape.textContent=content
                curShape.attributes.fill.value="#000000"

              }
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
