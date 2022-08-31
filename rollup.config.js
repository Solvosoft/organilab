import defaultConfig from './editor.rollup.config.js';

export default commandLineArgs => {
  if (commandLineArgs.configDebug === true) {
    return defaultConfig;  // debugConfig
  }
  return defaultConfig;
};