import JsBarcode from 'jsbarcode';
const name = 'barcode'

class BarcodeManager {
    constructor(svgCanvas){
        this.svgCanvas=svgCanvas;
    }

    calleventAddOrUpdateCode(instance){
        return instance.eventAddOrUpdateCode
    }

    findElement(){

    }

    eventAddOrUpdateCode(){
         let curShape=this.addelement()
       // barcodesvg.id= this.svgCanvas.getNextId()
       // document.body.append(barcodesvg)
        JsBarcode("#"+curShape.id, document.getElementById('id_barcode').value)
    }

    registerEvent(){
        document.getElementById('id_barcode').addEventListener('change',
        this.calleventAddOrUpdateCode(this)
        );
    }
    addelement(){
        const curStyle = this.svgCanvas.getStyle()
        const curShape = this.svgCanvas.addSVGElementsFromJson({
          element: 'g',
          curStyles: true,
          attr: { x:100, y:100,  height: 100,  width: 100,
                  class: 'barcode', id: this.svgCanvas.getNextId(),
                  opacity: curStyle.opacity
                }
        })

        return curShape
    }


}

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
    const modeId = 'tool_codebar'
    const plugId = 'ext-codebar'

    const barcodemanager = new BarcodeManager(svgCanvas)

    const insertAfter = (referenceNode, newNode) => {
      referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling)
    }

    return {
           name: svgEditor.i18next.t(`${name}:name`),
           callback () {
                barcodemanager.registerEvent()
                const btitle = `${name}:buttons.0.title`
                // Add the button and its handler(s)
                const buttonTemplate = document.createElement('template')
                buttonTemplate.innerHTML = `<se-button id="${plugId}" title="${btitle}" src="context_menu.svg"></se-button>`
                insertAfter($id('tool_zoom'), buttonTemplate.content.cloneNode(true))

                $click($id(`${plugId}`), () => {
                  if (this.leftPanel.updateLeftPanel(`${plugId}`)) {
                    barcodemanager.eventAddOrUpdateCode()
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
