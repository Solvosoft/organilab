/* eslint-env node */
// This rollup script is run by the command:
// 'npm run build'

import path from 'path'
import { lstatSync, readdirSync } from 'fs'
import rimraf from 'rimraf'
import babel from '@rollup/plugin-babel'
import copy from 'rollup-plugin-copy'
import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'
import url from '@rollup/plugin-url' // for XML/SVG files
import html from 'rollup-plugin-html'
import replace from 'rollup-plugin-replace-imports-with-vars'

import dynamicImportVars from '@rollup/plugin-dynamic-import-vars'
import { terser } from 'rollup-plugin-terser'
// import progress from 'rollup-plugin-progress';
//import filesize from 'rollup-plugin-filesize'

const globals = {
  '@svgedit/svgcanvas': "window.SvgCanvas",
}

// utility function
const getDirectories = (source) => {
  const isDirectory = (dir) => {
    return lstatSync(dir).isDirectory()
  }
  return readdirSync(source).map((name) => path.join(source, name)).filter((i) => isDirectory(i))
}

const dirPath = path.join(__dirname, '/assets/svgedit');

// capture the list of files to build for extensions and ext-locales
const extensionDirs = getDirectories(dirPath+'/src/editor/extensions')

const dest = ['src/sga/static/editor']
const rmdest = process.env.dest === 'rm'

if(rmdest){
// remove existing distribution
rimraf('./src/sga/static/editor', () => console.info('recreating static editor'))
}

// config for svgedit core module
const config = [{
  input: [dirPath+'/src/editor/Editor.js'],
  external: ['@svgedit/svgcanvas'],
  output: [
    {
      format: 'es',
      inlineDynamicImports: true,
      sourcemap: false,
      file: './src/sga/static/editor/Editor.js'
    },
  ],
  plugins: [
    copy({
      targets: [
         { src: dirPath+'/src/editor/locale', dest },
        { src: dirPath+'/src/editor/images', dest },
        { src: dirPath+'/src/editor/components/jgraduate/images', dest: dest.map((d) => `${d}/components/jgraduate`) },
      //  { src: dirPath+'/src/editor/extensions/ext-shapes/shapelib', dest: dest.map((d) => `${d}/extensions/ext-shapes`) },
      //  { src: dirPath+'/src/editor/extensions/ext-pictograms/shapelib', dest: dest.map((d) => `${d}/extensions/ext-pictograms`) },
        { src: dirPath+'/src/editor/svgedit.css', dest },
        { src: dirPath+'/src/editor/extensions', dest }
      ]
    }),
    html({
      include: [
        '../svgeditor/src/editor/panels/*.html',
        '../svgeditor/src/editor/templates/*.html',
        '../svgeditor/src/editor/dialogs/*.html'
      ]
    }),
    nodeResolve({
      browser: true,
      preferBuiltins: false
    }),
    commonjs(),
    replace({ varType: 'var', replacementLookup: globals }),
    dynamicImportVars({ include: dirPath+'/src/editor/locale.js' }),
    babel({ babelHelpers: 'bundled', exclude: [/\/core-js\//] }), // exclude core-js to avoid circular dependencies.
    terser({ keep_fnames: true }), // keep_fnames is needed to avoid an error when calling extensions.
    //filesize()

  ]
}
]

// config for dynamic extensions
extensionDirs.forEach((extensionDir) => {
  const extensionName = path.basename(extensionDir)
  extensionName && config.push(
    {
      input: `${dirPath}/src/editor/extensions/${extensionName}/${extensionName}.js`,
      output: [
        {
          format: 'es',
          dir: `../src/sga/static/editor/extensions/${extensionName}`,
          inlineDynamicImports: true,
          sourcemap: true
        }
      ],
      plugins: [
        url({
          include: ['**/*.svg', '**/*.xml'],
          limit: 0,
          fileName: '[name][extname]'
        }),
        html({
          include: [
            dirPath+'/src/editor/extensions/*/*.html'
          ]
        }),
        nodeResolve({
          browser: true,
          preferBuiltins: true
        }),
        commonjs({ exclude: `${dirPath}/src/editor/extensions/${extensionName}/${extensionName}.js` }),
        dynamicImportVars({ include: `${dirPath}/src/editor/extensions/${extensionName}/${extensionName}.js` }),
        babel({ babelHelpers: 'bundled', exclude: [/\/core-js\//] }),
        terser({ keep_fnames: true })
      ]
    }
  )
})

export default config
