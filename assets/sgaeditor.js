import Editor from '../editor/Editor.js';


const svgEditor = new Editor(document.getElementById('canvas_editor'))
svgEditor.init()
svgEditor.setConfig({
          allowInitialUserOverride: true,
          imgPath: '/static/editor/images',
          extPreurl: '/static/editor/',
          extensions: [],
          noDefaultExtensions: true,
          userExtensions: [
            {pathName: '/static/userextensions/text-multiline/text-multiline.js'},
            {pathName: '/static/userextensions/ext-pictograms/ext-pictograms.js'}
//            {pathName: '/static/userextensions/ext-text/ext-text.js'}
          /* {pathName: 'textoseleccionado-bundle.js'} { pathName: './react-extensions/react-test/dist/react-test.js' } */]
        })

