const config = [
{
input: 'assets/sgaeditor.js',
output: [
    {
      format: 'es',
      inlineDynamicImports: false,
      sourcemap: false,
      file: './src/sga/static/sga/sga-bundle.js'
    },
  ],
external: ['../editor/Editor.js', '../svgcanvas/svgcanvas.js']
}
]

export default config