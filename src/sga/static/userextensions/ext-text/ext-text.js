const name = 'textcodes'

const loadExtensionTranslation = async function (svgEditor) {
  let translationModule
  const lang = svgEditor.configObj.pref('lang')
  try {
    translationModule = await import(`./locale/${lang}.js`)
  } catch (_error) {
    console.warn(`Missing translation (${lang}) for ${name} - using 'en'`)
    translationModule = await import('./locale/en.js')
  }
  svgEditor.i18next.addResourceBundle(lang, name, translationModule.default)
}

export default {
  name,
  async init () {
    const svgEditor = this
    const { svgCanvas } = svgEditor
    const modeId = 'tool_textcodes'
    await loadExtensionTranslation(svgEditor)

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

        const textclass="textelementforeign"
        const curStyle = svgCanvas.getStyle()
        const curShape = svgCanvas.addSVGElementsFromJson({
                  element: 'foreignObject',
                  curStyles: true,
                  attr: {
                    x:100,
                    y:100,
                    height: 100,
                    width: 100,
                    class: textclass,
                    id: svgCanvas.getNextId(),
                    opacity: curStyle.opacity

                  }
              })
            curShape.innerHTML="<p>"+content+"</p>"
            curShape.addEventListener("dblclick", editText);
            svgCanvas.setSelectedElements(0, curShape)
            svgCanvas.setCurrentMode('select')
            svgEditor.leftPanel.updateLeftPanel('tool_select')


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
