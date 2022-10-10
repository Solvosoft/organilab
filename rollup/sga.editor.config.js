import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'

const config = [
{
input: 'assets/sgaeditor.js',
output: [
    {
      format: 'es',
      inlineDynamicImports: false,
      sourcemap: false,
      file: './src/sga/static/sga/sga-bundle.js',
      globals: {
          Editor: "'../editor/Editor.js'"
      }
    },
  ],
plugins: [
    nodeResolve({
      browser: true,
      preferBuiltins: false
    }),
    commonjs(),
],
external:  ['../editor/Editor.js'] //[, '../svgcanvas/svgcanvas.js']
}
]

export default config