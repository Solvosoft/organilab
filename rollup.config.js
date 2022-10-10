import EditorConfig from './rollup/editor.config.js';
import SgaEditorConfig from './rollup/sga.editor.config.js';

export default commandLineArgs => {
  if (commandLineArgs.configDebug === true) {
    return EditorConfig;
  }
  return SgaEditorConfig;  // debugConfig
};