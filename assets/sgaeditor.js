import Editor from 'svgedit/dist/editor/Editor';
import ExtSeleccionado from 'sga-editor-extension/texto_seleccionado/ext-texto_seleccionado';

const svgEditor = new Editor(document.getElementById('canvas_editor'))
svgEditor.init()
svgEditor.setConfig({
          allowInitialUserOverride: true,
          imgPath: '/static/editor/images',
          extensions: [],
          noDefaultExtensions: true,
          userExtensions: [

          /* {pathName: 'textoseleccionado-bundle.js'} { pathName: './react-extensions/react-test/dist/react-test.js' } */]
        })


svgEditor.extAdded(window, ExtSeleccionado);
// Variable XDOMAIN below is created by Rollup for the Xdomain build (see rollup.config.js)
/* globals XDOMAIN */
try { // try clause to avoid js to complain if XDOMAIN undefined
          if (XDOMAIN) {
            svgEditor.setConfig({
              canvasName: 'xdomain', // Namespace this
              allowedOrigins: [ '*' ]
            })
    console.info('xdomain config activated')
  }
} catch (error) { /* empty fn */ }