import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'
import path from 'path'

import babel from '@rollup/plugin-babel'
import { terser } from 'rollup-plugin-terser'
import copy from 'rollup-plugin-copy'

const dest = ['./src/sga/static/userextensions/ext-barcode/']
const dirPath = path.join(__dirname, '../assets/ext-barcode');
const config = [
{
input: dirPath+'/ext-barcode.js',
output: [
    {
      name: 'barcodemanager',
      format: 'es',
      inlineDynamicImports: true,
      sourcemap: false,
      file: './src/sga/static/userextensions/ext-barcode/ext-barcode.js'
    },
  ],
plugins: [
copy({
      targets: [
        { src: dirPath+'/locale', dest }
      ]
    }),

    nodeResolve({
      browser: true,
      preferBuiltins: false
    }),
    commonjs(),
    babel({ babelHelpers: 'bundled', exclude: [/\/core-js\//] }),
    terser({ keep_fnames: true })
]
}
]

export default config