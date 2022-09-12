import html2canvas from 'html2canvas';
import Editor from '../editor/Editor.js';

async function generateSVGfromTextArea(elem){
    // Capture specific element

    html2canvas(elem).then(canvas => {
        console.log(elem);
        console.log(canvas);
        //document.body.appendChild(canvas)
    });
}

const svgEditor = new Editor(document.getElementById('canvas_editor'))
svgEditor.init()
svgEditor.setConfig({
          allowInitialUserOverride: true,
          imgPath: '/static/editor/images',
          extPreurl: '/static/editor/',
          extensions: [],
          noDefaultExtensions: true,
          userExtensions: [
            {pathName: '/static/userextensions/text-multiline/text-multiline.js'}
          /* {pathName: 'textoseleccionado-bundle.js'} { pathName: './react-extensions/react-test/dist/react-test.js' } */]
        })

svgEditor.generateSVGfromTextArea=generateSVGfromTextArea;
