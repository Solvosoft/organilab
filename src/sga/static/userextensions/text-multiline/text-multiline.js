const name = 'textmultiline'

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
    await loadExtensionTranslation(svgEditor)
    const { svgCanvas } = svgEditor
    const { $id, $click } = svgCanvas
    const modeId = 'tool_multiline'
    const plugId = 'ext-textmultiline'
    const insertAfter = (referenceNode, newNode) => {
      referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling)
    }

    const editText = (event)=>{

         let selects = svgCanvas.getSelectedElements()
         if(selects.length==1 && selects[0].attributes.class.value=="textelementforeign"){
             tinymce.get("wyswygmodaltextarea").setContent(selects[0].innerHTML);
             $('#wyswygmodal').modal('show');
         }
    }
    const addText = (event)=>{
        let content = tinymce.get("wyswygmodaltextarea").getContent()
        let selects = svgCanvas.getSelectedElements()
        if(selects.length==1 && selects[0].attributes.class.value=="textelementforeign"){
            selects[0].innerHTML=content
        }else{


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
               curShape.innerHTML=content
            curShape.addEventListener("dblclick", editText);
            svgCanvas.setSelectedElements(0, curShape)
            svgCanvas.setCurrentMode('select')
            svgEditor.leftPanel.updateLeftPanel('tool_select')
            }
            $('#wyswygmodal').modal('hide');
    }

    document.getElementById("btnsave-multiline").addEventListener("click", addText);

    const addStyleText  = (elements) => {
        elements.forEach((htmlelement)=>{

            if(htmlelement.attributes.hasOwnProperty('data-mce-style') ){
               htmlelement.style.cssText = htmlelement.attributes['data-mce-style'].value
            }
            if(htmlelement.children !== undefined){
                    addStyleText(Array.from(htmlelement.children))
            }

        })
    }

    return {
           name: svgEditor.i18next.t(`${name}:name`),
       callback () {
            const btitle = `${name}:buttons.0.title`
            // Add the button and its handler(s)
            const buttonTemplate = document.createElement('template')
        buttonTemplate.innerHTML = `<se-button id="${plugId}" title="${btitle}" src="panning.svg"></se-button>`
         insertAfter($id('tool_zoom'), buttonTemplate.content.cloneNode(true))
        $click($id(`${plugId}`), () => {
          if (this.leftPanel.updateLeftPanel(`${plugId}`)) {
            svgCanvas.setMode(modeId)
            $('#wyswygmodal').modal();
          }
        })
      },
      mouseDown () {
       if (svgCanvas.getMode() === modeId) {
          return {
            started: true
          }
        }
        return undefined
      },
      mouseUp () {
        if (svgCanvas.getMode() === modeId) {
          return {
            keep: false,
            element: null
          }
        }
        return undefined
      }
    }
   }
 }


