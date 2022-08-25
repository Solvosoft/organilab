/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./assets/node_modules/sga-editor-extension/texto_seleccionado/ext-texto_seleccionado.js":
/*!***********************************************************************************************!*\
  !*** ./assets/node_modules/sga-editor-extension/texto_seleccionado/ext-texto_seleccionado.js ***!
  \***********************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/**\n * @file ext-grid.js\n *\n * @license Apache-2.0\n *\n * @copyright 2010 Redou Mine, 2010 Alexis Deveria\n *\n */\n\nconst name = 'seleccionado'\n\nconst loadExtensionTranslation = async function (svgEditor) {\n  let translationModule\n  const lang = svgEditor.configObj.pref('lang')\n  try {\n    translationModule = await __webpack_require__(\"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale lazy recursive ^\\\\.\\\\/.*\\\\.js$\")(`./${lang}.js`)\n  } catch (_error) {\n    console.warn(`Missing translation (${lang}) for ${name} - using 'en'`)\n    translationModule = await __webpack_require__.e(/*! import() */ \"assets_node_modules_sga-editor-extension_texto_seleccionado_locale_en_js\").then(__webpack_require__.bind(__webpack_require__, /*! ./locale/en.js */ \"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/en.js\"))\n  }\n  svgEditor.i18next.addResourceBundle(lang, name, translationModule.default)\n}\n\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ({\n  name,\n  async init () {\n    const svgEditor = this\n    await loadExtensionTranslation(svgEditor)\n    const { svgCanvas } = svgEditor\n    const { $id, $click, NS } = svgCanvas\n    const svgdoc = $id('svgcanvas').ownerDocument\n    const { assignAttributes } = svgCanvas\n    const hcanvas = document.createElement('canvas')\n    const canvBG = $id('canvasBackground')\n    const units = svgCanvas.getTypeMap() // Assumes prior `init()` call on `units.js` module\n    const intervals = [0.01, 0.1, 1, 10, 100, 1000]\n    let showGrid = svgEditor.configObj.curConfig.showGrid || false\n\n    hcanvas.style.display = 'none'\n    svgEditor.$svgEditor.appendChild(hcanvas)\n\n    const canvasGrid = svgdoc.createElementNS(NS.SVG, 'svg')\n    assignAttributes(canvasGrid, {\n      id: 'canvasGrid',\n      width: '100%',\n      height: '100%',\n      x: 0,\n      y: 0,\n      overflow: 'visible',\n      display: 'none'\n    })\n    canvBG.appendChild(canvasGrid)\n    const gridDefs = svgdoc.createElementNS(NS.SVG, 'defs')\n    // grid-pattern\n    const gridPattern = svgdoc.createElementNS(NS.SVG, 'pattern')\n    assignAttributes(gridPattern, {\n      id: 'gridpattern',\n      patternUnits: 'userSpaceOnUse',\n      x: 0, // -(value.strokeWidth / 2), // position for strokewidth\n      y: 0, // -(value.strokeWidth / 2), // position for strokewidth\n      width: 100,\n      height: 100\n    })\n\n    const gridimg = svgdoc.createElementNS(NS.SVG, 'image')\n    assignAttributes(gridimg, {\n      x: 0,\n      y: 0,\n      width: 100,\n      height: 100\n    })\n    gridPattern.append(gridimg)\n    gridDefs.append(gridPattern)\n    $id('canvasGrid').appendChild(gridDefs)\n\n    // grid-box\n    const gridBox = svgdoc.createElementNS(NS.SVG, 'rect')\n    assignAttributes(gridBox, {\n      width: '100%',\n      height: '100%',\n      x: 0,\n      y: 0,\n      'stroke-width': 0,\n      stroke: 'none',\n      fill: 'url(#gridpattern)',\n      style: 'pointer-events: none; display:visible;'\n    })\n    $id('canvasGrid').appendChild(gridBox)\n\n    /**\n     *\n     * @param {Float} zoom\n     * @returns {void}\n     */\n    const updateGrid = (zoom) => {\n      // TODO: Try this with <line> elements, then compare performance difference\n      const unit = units[svgEditor.configObj.curConfig.baseUnit] // 1 = 1px\n      const uMulti = unit * zoom\n      // Calculate the main number interval\n      const rawM = 100 / uMulti\n      let multi = 1\n      intervals.some((num) => {\n        multi = num\n        return rawM <= num\n      })\n      const bigInt = multi * uMulti\n\n      // Set the canvas size to the width of the container\n      hcanvas.width = bigInt\n      hcanvas.height = bigInt\n      const ctx = hcanvas.getContext('2d')\n      const curD = 0.5\n      const part = bigInt / 10\n\n      ctx.globalAlpha = 0.2\n      ctx.strokeStyle = svgEditor.configObj.curConfig.gridColor\n      for (let i = 1; i < 10; i++) {\n        const subD = Math.round(part * i) + 0.5\n        // const lineNum = (i % 2)?12:10;\n        const lineNum = 0\n        ctx.moveTo(subD, bigInt)\n        ctx.lineTo(subD, lineNum)\n        ctx.moveTo(bigInt, subD)\n        ctx.lineTo(lineNum, subD)\n      }\n      ctx.stroke()\n      ctx.beginPath()\n      ctx.globalAlpha = 0.5\n      ctx.moveTo(curD, bigInt)\n      ctx.lineTo(curD, 0)\n\n      ctx.moveTo(bigInt, curD)\n      ctx.lineTo(0, curD)\n      ctx.stroke()\n\n      const datauri = hcanvas.toDataURL('image/png')\n      gridimg.setAttribute('width', bigInt)\n      gridimg.setAttribute('height', bigInt)\n      gridimg.parentNode.setAttribute('width', bigInt)\n      gridimg.parentNode.setAttribute('height', bigInt)\n      svgCanvas.setHref(gridimg, datauri)\n    }\n\n    /**\n     *\n     * @returns {void}\n     */\n    const gridUpdate = () => {\n      if (showGrid) {\n        updateGrid(svgCanvas.getZoom())\n      }\n      $id('canvasGrid').style.display = (showGrid) ? 'block' : 'none'\n      $id('view_grid').pressed = showGrid\n    }\n    return {\n      name: svgEditor.i18next.t(`${name}:name`),\n      zoomChanged (zoom) {\n        if (showGrid) { updateGrid(zoom) }\n      },\n      callback () {\n        // Add the button and its handler(s)\n        const buttonTemplate = document.createElement('template')\n        const title = `${name}:buttons.0.title`\n        buttonTemplate.innerHTML = `\n          <se-button id=\"view_grid\" title=\"${title}\" src=\"grid.svg\"></se-button>\n        `\n        $id('editor_panel').append(buttonTemplate.content.cloneNode(true))\n        $click($id('view_grid'), () => {\n          svgEditor.configObj.curConfig.showGrid = showGrid = !showGrid\n          gridUpdate()\n        })\n        if (showGrid) {\n          gridUpdate()\n        }\n      }\n    }\n  }\n});\n\n//# sourceURL=webpack://organilab/./assets/node_modules/sga-editor-extension/texto_seleccionado/ext-texto_seleccionado.js?");

/***/ }),

/***/ "./assets/node_modules/sga-editor-extension/texto_seleccionado/locale lazy recursive ^\\.\\/.*\\.js$":
/*!****************************************************************************************************************!*\
  !*** ./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/ lazy ^\.\/.*\.js$ namespace object ***!
  \****************************************************************************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval("var map = {\n\t\"./en.js\": [\n\t\t\"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/en.js\",\n\t\t\"assets_node_modules_sga-editor-extension_texto_seleccionado_locale_en_js\"\n\t],\n\t\"./fr.js\": [\n\t\t\"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/fr.js\",\n\t\t\"assets_node_modules_sga-editor-extension_texto_seleccionado_locale_fr_js\"\n\t],\n\t\"./tr.js\": [\n\t\t\"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/tr.js\",\n\t\t\"assets_node_modules_sga-editor-extension_texto_seleccionado_locale_tr_js\"\n\t],\n\t\"./zh-CN.js\": [\n\t\t\"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/zh-CN.js\",\n\t\t\"assets_node_modules_sga-editor-extension_texto_seleccionado_locale_zh-CN_js\"\n\t]\n};\nfunction webpackAsyncContext(req) {\n\tif(!__webpack_require__.o(map, req)) {\n\t\treturn Promise.resolve().then(() => {\n\t\t\tvar e = new Error(\"Cannot find module '\" + req + \"'\");\n\t\t\te.code = 'MODULE_NOT_FOUND';\n\t\t\tthrow e;\n\t\t});\n\t}\n\n\tvar ids = map[req], id = ids[0];\n\treturn __webpack_require__.e(ids[1]).then(() => {\n\t\treturn __webpack_require__(id);\n\t});\n}\nwebpackAsyncContext.keys = () => (Object.keys(map));\nwebpackAsyncContext.id = \"./assets/node_modules/sga-editor-extension/texto_seleccionado/locale lazy recursive ^\\\\.\\\\/.*\\\\.js$\";\nmodule.exports = webpackAsyncContext;\n\n//# sourceURL=webpack://organilab/./assets/node_modules/sga-editor-extension/texto_seleccionado/locale/_lazy_^\\.\\/.*\\.js$_namespace_object?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = __webpack_modules__;
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/ensure chunk */
/******/ 	(() => {
/******/ 		__webpack_require__.f = {};
/******/ 		// This file contains only the entry chunk.
/******/ 		// The chunk loading function for additional chunks
/******/ 		__webpack_require__.e = (chunkId) => {
/******/ 			return Promise.all(Object.keys(__webpack_require__.f).reduce((promises, key) => {
/******/ 				__webpack_require__.f[key](chunkId, promises);
/******/ 				return promises;
/******/ 			}, []));
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/get javascript chunk filename */
/******/ 	(() => {
/******/ 		// This function allow to reference async chunks
/******/ 		__webpack_require__.u = (chunkId) => {
/******/ 			// return url for filenames based on template
/******/ 			return "" + chunkId + "-bundle.js";
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/global */
/******/ 	(() => {
/******/ 		__webpack_require__.g = (function() {
/******/ 			if (typeof globalThis === 'object') return globalThis;
/******/ 			try {
/******/ 				return this || new Function('return this')();
/******/ 			} catch (e) {
/******/ 				if (typeof window === 'object') return window;
/******/ 			}
/******/ 		})();
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/load script */
/******/ 	(() => {
/******/ 		var inProgress = {};
/******/ 		var dataWebpackPrefix = "organilab:";
/******/ 		// loadScript function to load a script via script tag
/******/ 		__webpack_require__.l = (url, done, key, chunkId) => {
/******/ 			if(inProgress[url]) { inProgress[url].push(done); return; }
/******/ 			var script, needAttach;
/******/ 			if(key !== undefined) {
/******/ 				var scripts = document.getElementsByTagName("script");
/******/ 				for(var i = 0; i < scripts.length; i++) {
/******/ 					var s = scripts[i];
/******/ 					if(s.getAttribute("src") == url || s.getAttribute("data-webpack") == dataWebpackPrefix + key) { script = s; break; }
/******/ 				}
/******/ 			}
/******/ 			if(!script) {
/******/ 				needAttach = true;
/******/ 				script = document.createElement('script');
/******/ 		
/******/ 				script.charset = 'utf-8';
/******/ 				script.timeout = 120;
/******/ 				if (__webpack_require__.nc) {
/******/ 					script.setAttribute("nonce", __webpack_require__.nc);
/******/ 				}
/******/ 				script.setAttribute("data-webpack", dataWebpackPrefix + key);
/******/ 				script.src = url;
/******/ 			}
/******/ 			inProgress[url] = [done];
/******/ 			var onScriptComplete = (prev, event) => {
/******/ 				// avoid mem leaks in IE.
/******/ 				script.onerror = script.onload = null;
/******/ 				clearTimeout(timeout);
/******/ 				var doneFns = inProgress[url];
/******/ 				delete inProgress[url];
/******/ 				script.parentNode && script.parentNode.removeChild(script);
/******/ 				doneFns && doneFns.forEach((fn) => (fn(event)));
/******/ 				if(prev) return prev(event);
/******/ 			}
/******/ 			;
/******/ 			var timeout = setTimeout(onScriptComplete.bind(null, undefined, { type: 'timeout', target: script }), 120000);
/******/ 			script.onerror = onScriptComplete.bind(null, script.onerror);
/******/ 			script.onload = onScriptComplete.bind(null, script.onload);
/******/ 			needAttach && document.head.appendChild(script);
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/publicPath */
/******/ 	(() => {
/******/ 		var scriptUrl;
/******/ 		if (__webpack_require__.g.importScripts) scriptUrl = __webpack_require__.g.location + "";
/******/ 		var document = __webpack_require__.g.document;
/******/ 		if (!scriptUrl && document) {
/******/ 			if (document.currentScript)
/******/ 				scriptUrl = document.currentScript.src
/******/ 			if (!scriptUrl) {
/******/ 				var scripts = document.getElementsByTagName("script");
/******/ 				if(scripts.length) scriptUrl = scripts[scripts.length - 1].src
/******/ 			}
/******/ 		}
/******/ 		// When supporting browsers where an automatic publicPath is not supported you must specify an output.publicPath manually via configuration
/******/ 		// or pass an empty string ("") and set the __webpack_public_path__ variable from your code to use your own logic.
/******/ 		if (!scriptUrl) throw new Error("Automatic publicPath is not supported in this browser");
/******/ 		scriptUrl = scriptUrl.replace(/#.*$/, "").replace(/\?.*$/, "").replace(/\/[^\/]+$/, "/");
/******/ 		__webpack_require__.p = scriptUrl;
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/jsonp chunk loading */
/******/ 	(() => {
/******/ 		// no baseURI
/******/ 		
/******/ 		// object to store loaded and loading chunks
/******/ 		// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 		// [resolve, reject, Promise] = chunk loading, 0 = chunk loaded
/******/ 		var installedChunks = {
/******/ 			"textoseleccionado": 0
/******/ 		};
/******/ 		
/******/ 		__webpack_require__.f.j = (chunkId, promises) => {
/******/ 				// JSONP chunk loading for javascript
/******/ 				var installedChunkData = __webpack_require__.o(installedChunks, chunkId) ? installedChunks[chunkId] : undefined;
/******/ 				if(installedChunkData !== 0) { // 0 means "already installed".
/******/ 		
/******/ 					// a Promise means "currently loading".
/******/ 					if(installedChunkData) {
/******/ 						promises.push(installedChunkData[2]);
/******/ 					} else {
/******/ 						if(true) { // all chunks have JS
/******/ 							// setup Promise in chunk cache
/******/ 							var promise = new Promise((resolve, reject) => (installedChunkData = installedChunks[chunkId] = [resolve, reject]));
/******/ 							promises.push(installedChunkData[2] = promise);
/******/ 		
/******/ 							// start chunk loading
/******/ 							var url = __webpack_require__.p + __webpack_require__.u(chunkId);
/******/ 							// create error before stack unwound to get useful stacktrace later
/******/ 							var error = new Error();
/******/ 							var loadingEnded = (event) => {
/******/ 								if(__webpack_require__.o(installedChunks, chunkId)) {
/******/ 									installedChunkData = installedChunks[chunkId];
/******/ 									if(installedChunkData !== 0) installedChunks[chunkId] = undefined;
/******/ 									if(installedChunkData) {
/******/ 										var errorType = event && (event.type === 'load' ? 'missing' : event.type);
/******/ 										var realSrc = event && event.target && event.target.src;
/******/ 										error.message = 'Loading chunk ' + chunkId + ' failed.\n(' + errorType + ': ' + realSrc + ')';
/******/ 										error.name = 'ChunkLoadError';
/******/ 										error.type = errorType;
/******/ 										error.request = realSrc;
/******/ 										installedChunkData[1](error);
/******/ 									}
/******/ 								}
/******/ 							};
/******/ 							__webpack_require__.l(url, loadingEnded, "chunk-" + chunkId, chunkId);
/******/ 						} else installedChunks[chunkId] = 0;
/******/ 					}
/******/ 				}
/******/ 		};
/******/ 		
/******/ 		// no prefetching
/******/ 		
/******/ 		// no preloaded
/******/ 		
/******/ 		// no HMR
/******/ 		
/******/ 		// no HMR manifest
/******/ 		
/******/ 		// no on chunks loaded
/******/ 		
/******/ 		// install a JSONP callback for chunk loading
/******/ 		var webpackJsonpCallback = (parentChunkLoadingFunction, data) => {
/******/ 			var [chunkIds, moreModules, runtime] = data;
/******/ 			// add "moreModules" to the modules object,
/******/ 			// then flag all "chunkIds" as loaded and fire callback
/******/ 			var moduleId, chunkId, i = 0;
/******/ 			if(chunkIds.some((id) => (installedChunks[id] !== 0))) {
/******/ 				for(moduleId in moreModules) {
/******/ 					if(__webpack_require__.o(moreModules, moduleId)) {
/******/ 						__webpack_require__.m[moduleId] = moreModules[moduleId];
/******/ 					}
/******/ 				}
/******/ 				if(runtime) var result = runtime(__webpack_require__);
/******/ 			}
/******/ 			if(parentChunkLoadingFunction) parentChunkLoadingFunction(data);
/******/ 			for(;i < chunkIds.length; i++) {
/******/ 				chunkId = chunkIds[i];
/******/ 				if(__webpack_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 					installedChunks[chunkId][0]();
/******/ 				}
/******/ 				installedChunks[chunkId] = 0;
/******/ 			}
/******/ 		
/******/ 		}
/******/ 		
/******/ 		var chunkLoadingGlobal = self["webpackChunkorganilab"] = self["webpackChunkorganilab"] || [];
/******/ 		chunkLoadingGlobal.forEach(webpackJsonpCallback.bind(null, 0));
/******/ 		chunkLoadingGlobal.push = webpackJsonpCallback.bind(null, chunkLoadingGlobal.push.bind(chunkLoadingGlobal));
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = __webpack_require__("./assets/node_modules/sga-editor-extension/texto_seleccionado/ext-texto_seleccionado.js");
/******/ 	
/******/ })()
;