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

    const addText = (event)=>{
        alert(svgEditor.generateSVGfromTextArea(document.getElementById("wyswygmodaltextarea")))
    }

    document.getElementById("btnsave-multiline").addEventListener("click", addText);

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
          svgEditor.setPanning(true)
          return {
            started: true
          }
        }
        return undefined
      },
      mouseUp () {
        if (svgCanvas.getMode() === modeId) {
          svgEditor.setPanning(false)
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


