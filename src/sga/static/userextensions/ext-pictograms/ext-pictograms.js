/**
 * @file ext-pictograms.js
 *
 * @license MIT
 *
 * @copyright 2022 Luis Zarate Montero
 *
 */

const name = 'pictograms'

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
    const canv = svgEditor.svgCanvas
    const { $id, $click } = canv
    const svgroot = canv.getSvgRoot()
    let lastBBox = {}
    await loadExtensionTranslation(svgEditor)

    const modeId = 'tool_pictogram'
    const startClientPos = {}

    const getImageG=(image)=>{
        image = image.replace("data:image/svg+xml;base64,", "")
        var doc = new DOMParser().parseFromString(atob(image), "text/xml");

        return doc
    }
    let curShape
    let startX
    let startY

    return {
      callback () {	
        if ($id('tool_pictogram') === null) {
          const extPath = svgEditor.configObj.curConfig.extPath
          const buttonTemplate = `<se-explorerbutton id="tool_pictogram" title="pictogram" lib="../userextensions/ext-pictograms/shapelib/" src="warning.svg"></se-explorerbutton>`
          canv.insertChildAtIndex($id('tools_left'), buttonTemplate	)
          $click($id('tool_pictogram'), () => {
            if (this.leftPanel.updateLeftPanel('tool_pictogram')) {
              canv.setMode(modeId)
            }
          })
        }
      },
      mouseDown (opts) {
        const mode = canv.getMode()
        if (mode !== modeId) { return undefined }

        startX = opts.start_x
        const x = startX
        startY = opts.start_y
        const y = startY
        startClientPos.x = opts.event.clientX 
        startClientPos.y = opts.event.clientY
        
        const curStyle = canv.getStyle()
        
        var currentD = document.getElementById('tool_pictogram').dataset.draw
        if (currentD.endsWith('.svg')){
				
	    canv.setStarted(true)

        curShape = canv.addSVGElementsFromJson({
					element: 'g',
					attr: {
					  class: "pictogram",
					  id: canv.getNextId()
					}
				  })
		let dom =getImageG(document.getElementById('tool_pictogram').$img.src)
//		let viewport=dom.firstChild.firstElementChild;
//		viewport.attributes.removeNamedItem('height')
//		viewport.attributes.removeNamedItem('width')
//		viewport.attributes.removeNamedItem('viewBox')
//		curShape.appendChild(viewport)
		if (dom.firstChild.firstElementChild.childElementCount<2) {
            curShape.appendChild(dom.firstChild.firstElementChild.firstElementChild)
		}else{
    	    curShape.appendChild(dom.firstChild.firstElementChild.lastElementChild)
        }
		canv.setSelectedElements(0, curShape)
        canv.uniquifyElems(curShape)

		canv.setCurrentMode('select')
        svgEditor.leftPanel.updateLeftPanel('tool_select')

		}else{

		curShape = canv.addSVGElementsFromJson({
          element: 'path',
          curStyles: true,
          attr: {
            d: currentD,
            id: canv.getNextId(),
            opacity: curStyle.opacity / 2,
            style: 'pointer-events:none'
          }
        })

			}
        return {
          started: true
        }
      },
      mouseMove (opts) {
        const mode = canv.getMode()
        if (mode !== modeId) { return }


        const zoom = canv.getZoom()
        const evt = opts.event

        const x = opts.mouse_x / zoom
        const y = opts.mouse_y / zoom

        const tlist = curShape.transform.baseVal
        const box = curShape.getBBox()
        const left = box.x; const top = box.y

        const newbox = {
          x: Math.min(startX, x),
          y: Math.min(startY, y),
          width: Math.abs(x - startX),
          height: Math.abs(y - startY)
        }

        let sx = (newbox.width / lastBBox.width) || 1
        let sy = (newbox.height / lastBBox.height) || 1

        // Not perfect, but mostly works...
        let tx = 0
        if (x < startX) {
          tx = lastBBox.width
        }
        let ty = 0
        if (y < startY) {
          ty = lastBBox.height
        }


        // update the transform list with translate,scale,translate
        const translateOrigin = svgroot.createSVGTransform()
        const scale = svgroot.createSVGTransform()
        const translateBack = svgroot.createSVGTransform()

        translateOrigin.setTranslate(-(left + tx), -(top + ty))
        if (!evt.shiftKey) {
          const max = Math.min(Math.abs(sx), Math.abs(sy))

          sx = max * (sx < 0 ? -1 : 1)
          sy = max * (sy < 0 ? -1 : 1)
        }
        //scale.setScale(sx || 1, sy || 1)
		scale.setScale(1, 1)
        translateBack.setTranslate(left + tx, top + ty)
        tlist.appendItem(translateBack)
        tlist.appendItem(scale)
        tlist.appendItem(translateOrigin)

        canv.recalculateDimensions(curShape)

        lastBBox = curShape.getBBox()
      
      },
      mouseUp (opts) {
        const mode = canv.getMode()
        if (mode !== modeId) { return undefined }

        const keepObject = (opts.event.clientX !== startClientPos.x && opts.event.clientY !== startClientPos.y)

        return {
          keep: keepObject,
          element: curShape,
          started: false
        }
      }
    }
  }
}
