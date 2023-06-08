(function () {
	'use strict';

	const ShapeSmbl = Symbol('shape');

	/** @typedef {SVGGraphicsElement & { [ShapeSmbl]?: import('./shape-evt-proc').Shape }} ShapeElement */

	//
	// dom utils

	/**
	 * @template T
	 * @param {Element} parent
	 * @param {string} key
	 * @returns T
	 */
	const child = (parent, key) => /** @type {T} */(parent.querySelector(`[data-key="${key}"]`));

	/** @param {HTMLElement|SVGElement} crcl, @param {Point} pos */
	function positionSet(crcl, pos) { crcl.style.transform = `translate(${pos.x}px, ${pos.y}px)`; }

	/** @param {Element} el, @param {string[]} cl */
	const classAdd = (el, ...cl) => el?.classList.add(...cl);

	/** @param {Element} el, @param {string} cl */
	const classDel = (el, cl) => el?.classList.remove(cl);

	/** @param {Element | GlobalEventHandlers} el, @param {string} type, @param {EventListenerOrEventListenerObject} listener, @param {boolean?=} once */
	const listen = (el, type, listener, once) => el.addEventListener(type, listener, { passive: true, once });

	/** @param {Element | GlobalEventHandlers} el, @param {string} type, @param {EventListenerOrEventListenerObject} listener, @param {boolean?=} capture */
	const listenDel = (el, type, listener, capture) => el?.removeEventListener(type, listener, { capture });

	/** @param {ParentNode} el, @param {string} selector, @param {(this: GlobalEventHandlers, ev: PointerEvent & { currentTarget: Element }) => any} handler */
	function clickForAll(el, selector, handler) { el.querySelectorAll(selector).forEach(/** @param {HTMLElement} el */ el => { el.onclick = handler; }); }

	/** @param {ParentNode} el, @param {string} selector, @param {(this: GlobalEventHandlers, ev: PointerEvent & { currentTarget: Element }) => any} handler */
	function changeForAll(el, selector, handler) { el.querySelectorAll(selector).forEach(/** @param {HTMLElement} el */ el => { el.onchange = handler; }); }

	/** @param {PointerEvent & { currentTarget: Element }} evt, @param {string} attr */
	const evtTargetAttr = (evt, attr) => evt.currentTarget.getAttribute(attr);

	/**
	 * @template {keyof SVGElementTagNameMap} T
	 * @param {T} qualifiedName
	 * @param {string?=} innerHTML
	 * @returns {SVGElementTagNameMap[T]}
	 */
	function svgEl(qualifiedName, innerHTML) {
		const svgGrp = document.createElementNS('http://www.w3.org/2000/svg', qualifiedName);
		if (innerHTML) { svgGrp.innerHTML = innerHTML; }
		return svgGrp;
	}

	/**
	 * calc farthest point of <tspan>s bbox in {textEl}
	 * origin is in the center
	 * @param {SVGTextElement} textEl
	 */
	function svgTxtFarthestPoint(textEl) {
		/** @type {Point} */
		let maxPoint;
		let maxAbsSum = 0;
		for (const span of textEl.getElementsByTagName('tspan')) {
			for (const point of boxPoints(span.getBBox())) {
				const pointAbsSum = Math.abs(point.x) + Math.abs(point.y);
				if (maxAbsSum < pointAbsSum) {
					maxPoint = point;
					maxAbsSum = pointAbsSum;
				}
			}
		}
		return maxPoint;
	}

	/** @param {DOMRect} box */
	const boxPoints = (box) => [
		{ x: box.x, y: box.y },
		{ x: box.right, y: box.y },
		{ x: box.x, y: box.bottom },
		{ x: box.right, y: box.bottom }
	];

	//
	// math, arr utils

	/**
	 * Get the ceiling for a number {val} with a given floor height {step}
	 * @param {number} min
	 * @param {number} step
	 * @param {number} val
	 */
	function ceil(min, step, val) {
		if (val <= min) { return min; }
		return min + Math.ceil((val - min) / step) * step;
	}

	/**
	 * @template T
	 * @param {Array<T>} arr
	 * @param {{(el:T):void}} action
	 */
	function arrPop(arr, action) {
		let itm = arr.pop();
		while (itm) { action(itm); itm = arr.pop(); }}

	/** @param {Point} point, @param {Point} shift, @param {number=} coef */
	function pointShift(point, shift, coef) {
		const _coef = coef ?? 1;
		point.x += _coef * shift.x;
		point.y += _coef * shift.y;
		return point;
	}

	//
	// object utils

	/**
	 * @template T
	 * @param {T} obj
	 * @returns {T}
	 */
	const deepCopy = obj => JSON.parse(JSON.stringify(obj));


	/** @param {Element} shapeEl, @param {{a?:1|2|3}} shapeData, @param {Element} alignEl, @param {integer} alignSelection */
	function textAlign(shapeEl, shapeData, alignEl, alignSelection){
		const alignNew = alignSelection;
		if (alignNew === shapeData.a) { return; }

		const alignOld = shapeData.a;

		// applay text align to shape
		shapeData.a = alignNew;
		shapeEl[ShapeSmbl].draw();

		// highlight text align btn in settings panel
		classDel(alignEl, `ta-${alignOld}`);
		classAdd(alignEl, `ta-${shapeData.a}`);
	}

	/** @param {Element} shapeEl, @param {{ff?:string}} shapeData, @param {string} fontFamily */
	function applyFontFamily(shapeEl, shapeData, fontFamily){
		const txtEl = child(shapeEl, 'text');
		const txtAreaEl = child(shapeEl, 'textarea');
		shapeData.ff = txtEl.style.fontFamily = fontFamily;
		txtAreaEl.dispatchEvent(new Event('input'));  // so it gets updated with the new properties and the shape is resized accordingly
	}

	/** @param {Element} shapeEl, @param {{fs?:string}} shapeData, @param {string} fontSize */
	function applyFontSize(shapeEl, shapeData, fontSize){
		const txtEl = child(shapeEl, 'text');
		const txtAreaEl = child(shapeEl, 'textarea');
		shapeData.fs = txtEl.style.fontSize = fontSize;
		txtAreaEl.dispatchEvent(new Event('input'));  // so it gets updated with the new properties and the shape is resized accordingly
	}

	/** @param {Element} shapeEl, @param {{fc?:string}} shapeData, @param {string} fontColor */
	function applyFontColor(shapeEl, shapeData, fontColor){
		const txtEl = child(shapeEl, 'text');
		shapeData.fc = txtEl.style.fill = fontColor;
	}

	/** @param {Element} pathEl, @param {{sw?:float}} pathData, @param {float} strokeWidth */
	function applyPathStrokeWidth(pathEl, pathData, strokeWidth){
		const path = child(pathEl, 'path');
		const outer = child(pathEl, 'outer');
		const highlight = child(pathEl, 'highlight');
		const end = child(pathEl, 'arrow-end');
		const start = child(pathEl, "arrow-start");
		pathData.sw = path.style.strokeWidth = start.style.strokeWidth = end.style.strokeWidth = strokeWidth;
		highlight.style.strokeWidth = outer.style.strokeWidth = strokeWidth + 8;  // + 8 to give it some padding
	}

	/** @param {Element} shapeEl, @param {{bc?:string}} shapeData, @param {string} borderColor */
	function applyBorderColor(shapeEl, shapeData, borderColor){
		const mainEl = child(shapeEl, 'main');
		shapeData.bc = mainEl.style.stroke = borderColor;
	}

	/** @param {Element} shapeEl, @param {{bw?:float}} shapeData, @param {float} borderWidth */
	function applyBorderWidth(shapeEl, shapeData, borderWidth){
		const mainEl = child(shapeEl, 'main');
		const highlightEl = child(shapeEl, 'highlight');
		shapeData.bw = mainEl.style.strokeWidth = borderWidth;
		highlightEl.style.strokeWidth = borderWidth + 10;  // +10 to give it some extra padding so it is always visible
	}

	/** @param {Element} element, @param {string} action */
	function arrangeElement(element, action){
		switch (action) {
			case "bring-front":
				element.parentElement.appendChild(element);
				break;
			case "send-back":
				element.parentElement.prepend(element);
				break;
		}
	}

	/** @param {Element} shapeEl, @param {{ts?:string[]}} shapeData, @param {string} style, @param {Element} txtStyleEl  */
	function applyTxtStyle(shapeEl, shapeData, style, txtStyleEl){
		const index = shapeData.ts.indexOf(style);
		if(index > -1) {  // it is present in the array already, so it is a deselect
			shapeData.ts.splice(index, 1);
			classDel(shapeEl, `ts-${style}`);

			// dehighlight text style btn in settings panel
			classDel(txtStyleEl, `ts-${style}`);

		}else {  // it is a select
			shapeData.ts.push(style);
			classAdd(shapeEl, `ts-${style}`);

			// highlight text style btn in settings panel
			classAdd(txtStyleEl, `ts-${style}`);
		}
		const txtAreaEl = child(shapeEl, 'textarea');
		txtAreaEl.dispatchEvent(new Event('input'));  // so it gets updated with the new properties and the shape is resized accordingly
	}

	/** @param {Element} element, @param {{sc?:string}} elementData, @param {string} elementColor, @param {string} typeElement*/
	function applyElementColor(element, elementData, elementColor, typeElement){
		switch (typeElement) {
			case "shape":
				var mainEl = child(element, 'main');
				mainEl.style.fill = elementColor;
				break;
			case "path":
				var mainEl = child(element, 'path');
				var arrowStartEl = child(element, "arrow-start");
				var arrowEndEl = child(element, "arrow-end");
				mainEl.style.stroke = arrowStartEl.style.fill = arrowStartEl.style.stroke = arrowEndEl.style.stroke = arrowEndEl.style.fill = elementColor;
				break;
		}
		elementData.sc = elementColor;
	}

	/** @param {string} pictogramFillValue */
	function getPictogramIdFromFillValue(pictogramFillValue){
		return pictogramFillValue == "lavender" ? "default" : pictogramFillValue.substr(5, pictogramFillValue.length-6);
	}

	// setPictogram(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg)
	/** @param {Element} shapeEl, @param {{pic?:string[]}} shapeData, @param {string} pictogramFillValue, @param {Element} pictogramSelectEl  */
	function setPictogram(shapeEl, shapeData, pictogramFillValue, pictogramSelectEl){
		const mainEl = child(shapeEl, 'main');
		mainEl.style.fill = shapeData.pic = pictogramFillValue;

		// setup the class to the selected one so it is displayed correctly in the menu
		classDel(pictogramSelectEl.querySelector(".selected"), "selected");  // remove previous selection
		classAdd(pictogramSelectEl.querySelector(`#${getPictogramIdFromFillValue(pictogramFillValue)}`), 'selected');
	}

	/** @typedef { {x:number, y:number} } Point */

	/** @param {Element} elem */
	function moveEvtMobileFix(elem) {
		/** @type {Point} */ let pointDown;
		/** @type {number} */ let prevX;
		/** @type {number} */ let prevY;

		/** @param {PointerEventFixMovement} evt */
		function move(evt) {
			if (!evt.isPrimary || !evt.isTrusted) { return; }

			// fix old Android
			if (pointDown &&
					Math.abs(pointDown.x - evt.clientX) < 3 &&
					Math.abs(pointDown.y - evt.clientY) < 3) {
				evt.stopImmediatePropagation();
				return;
			}
			pointDown = null;

			// fix iOS
			if (evt.movementX === undefined) {
				evt[MovementXSmbl] = (prevX ? evt.clientX - prevX : 0);
				evt[MovementYSmbl] = (prevY ? evt.clientY - prevY : 0);
				prevX = evt.clientX;
				prevY = evt.clientY;
			} else {
				evt[MovementXSmbl] = evt.movementX;
				evt[MovementYSmbl] = evt.movementY;
			}
		}

		elem.addEventListener('pointerdown', /** @param {PointerEvent} evt */ evt => {
			pointDown = { x: evt.clientX, y: evt.clientY };
			prevX = null;
			prevY = null;
			elem.addEventListener('pointermove', move, { capture: true, passive: true });

			elem.addEventListener('pointerup', _ => {
				listenDel(elem, 'pointermove', move, true);
			}, { capture: true, once: true, passive: true });
		}, { capture: true, passive: true });
	}

	const MovementXSmbl = Symbol('movementX');
	const MovementYSmbl = Symbol('movementY');
	/** @typedef {PointerEvent & { [MovementXSmbl]: number, [MovementYSmbl]: number }} PointerEventFixMovement */

	/** @typedef { {x:number, y:number} } Point */

	const CanvasSmbl = Symbol('Canvas');

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef {{position:Point, scale:number, cell: number}} CanvasData */
	/** @typedef {SVGGElement & { [CanvasSmbl]?: Canvas }} CanvasElement */
	/**
	@typedef {{
		move?(x:number, y:number, scale:number): void
		data: CanvasData

		// TODO: it is not infrastructure methods -> shouldn't be here
		selectClear?(): void
		shapeMap: Record<string, import("../shapes/shape-type-map").ShapeType>
	}} Canvas
	*/

	/**
	 * @param { Element } elemTrackOutdown poitdows in this element will be tracking to fire {onOutdown} callback
	 * @param { Element } elem
	 * @param { {scale:number} } canvasScale
	 * @param { Point } shapePosition
	 * @param { {(evt:PointerEvent):void} } onMoveStart
	 * @param { {(evt:PointerEvent):void} } onMove
	 * @param { {(evt:PointerEvent):void} } onMoveEnd
	 * @param { {(evt:PointerEvent):void} } onClick
	 * @param { {():void} } onOutdown
	 */
	function moveEvtProc(elemTrackOutdown, elem, canvasScale, shapePosition, onMoveStart, onMove, onMoveEnd, onClick, onOutdown) {
		let isMoved = false;
		let isInit = false;
		let mouseDownPoint = {};
		/** @type {Element} */ let target;

		/** @param {PointerEventFixMovement} evt */
		function move(evt) {
			if (!isInit) { return; }

			if (!isMoved) {
				onMoveStart(evt);

				// if reset
				if (!isInit) { return; }
			}

			movementApplay(shapePosition, canvasScale.scale, evt);
			isMoved = true;
			onMove(evt);
		}

		/** @param {PointerEvent} evt */
		function cancel(evt) {
			if (isMoved) {
				onMoveEnd(evt);
			} else {
				onClick(evt);
			}
			reset(true);
		}

		/** @param {PointerEvent & { target:Node}} docEvt */
		function docDown(docEvt) {
			if (!elem.contains(docEvt.target)) {
				reset();
				onOutdown();
			}else {  // save current mouse point to use in case of a manual resize 
				mouseDownPoint = {
					x: docEvt.clientX,
					y: docEvt.clientY
				};
			}
		}

		function wheel() {
			reset();
			onOutdown();
		}

		/**
		 * @param {PointerEvent} evt
		*/
		function manualResize(evt){
			const direction = Number.parseInt(evt.target.getAttribute("data-resize-dir"));
			const shape = evt.target.parentNode[ShapeSmbl];
			const currentPoint = {x: evt.clientX, y: evt.clientY};
			const size = shape.calculateSizeForManualResize(shape.data, mouseDownPoint, currentPoint, direction);
			Object.keys(size).map(key => {  // reset the size properties required (it might be more than one) - so they are considered in draw
				if (key in shape.data) {
				  shape.data[key] = size[key];
				}
			});
			shape.draw();
			shape.data.ar = false;  // it was manually resized at least once, it doesn't need to be autoresized anymore
			mouseDownPoint = currentPoint;  // so it is considered in the new calculation if the user keeps resizing 
		}

		/**
		 * @param {ProcEvent} evt
		 */
		function init(evt) {
			if (evt[ProcessedSmbl] || !evt.isPrimary) {
				return;
			}

			evt[ProcessedSmbl] = true;
			target = /** @type {Element} */(evt.target);
			if (evt.pointerId !== fakePointerId) { target.setPointerCapture(evt.pointerId); }
			listen(target, 'pointercancel', cancel, true);
			listen(target, 'pointerup', cancel, true);
			listen(elemTrackOutdown, 'wheel', wheel, true);
			listen(elemTrackOutdown, 'pointerdown', docDown);
			if(target && target.getAttribute("data-shape-resize") != null){  // the move action is different for a resize
				listen(target, 'pointermove', manualResize);
			}else {
				listen(target, 'pointermove', move);
			}
			isInit = true;
		}

		listen(elem, 'pointerdown', init);

		/** @param {boolean} saveOutTrack */
		function reset(saveOutTrack) {
			listenDel(target, 'pointercancel', cancel);
			listenDel(target, 'pointerup', cancel);
			listenDel(target, 'pointermove', move);
			listenDel(target, 'pointermove', manualResize);
			if (!saveOutTrack) {
				listenDel(elemTrackOutdown, 'pointerdown', docDown);
				listenDel(elemTrackOutdown, 'wheel', wheel);
			}
			target = null;
			isMoved = false;
			isInit = false;
		}

		return reset;
	}

	/** @param {Point} point, @param {number} scale, @param {PointerEventFixMovement} evt */
	function movementApplay(point, scale, evt) {
		point.x += evt[MovementXSmbl] / scale;
		point.y += evt[MovementYSmbl] / scale;
	}

	const fakePointerId = 42; // random number
	/** @param {SVGGraphicsElement} shapeOrPathEl */
	function shapeSelect(shapeOrPathEl) {
		shapeOrPathEl.ownerSVGElement.focus();
		shapeOrPathEl.dispatchEvent(new PointerEvent('pointerdown', { isPrimary: true, pointerId: fakePointerId }));
		shapeOrPathEl.dispatchEvent(new PointerEvent('pointerup', { isPrimary: true }));
	}

	const ProcessedSmbl = Symbol('processed');

	/** @typedef {PointerEvent & { [ProcessedSmbl]?: boolean }} ProcEvent */
	/** @typedef {import('./move-evt-mobile-fix.js').PointerEventFixMovement} PointerEventFixMovement */
	/** @typedef { {x:number, y:number} } Point */

	/**
	 * Get point in canvas given the scale and position of the canvas
	 * @param {{position:{x:number, y:number}, scale:number}} canvasData
	 * @param {number} x, @param {number} y
	 */
	const pointInCanvas = (canvasData, x, y) => ({
		x: (x - canvasData.position.x) / canvasData.scale,
		y: (y - canvasData.position.y) / canvasData.scale
	});

	/**
	 * @param {Point} point
	 * @param {number} cell
	 */
	function placeToCell(point, cell) {
		const cellSizeHalf = cell / 2;
		function placeToCell(coordinate) {
			const coor = (Math.round(coordinate / cell) * cell);
			return (coordinate - coor > 0) ? coor + cellSizeHalf : coor - cellSizeHalf;
		}

		point.x = placeToCell(point.x);
		point.y = placeToCell(point.y);
	}

	/** @param { CanvasElement } canvas */
	function moveScaleApplay(canvas) {
		const canvasData = canvas[CanvasSmbl].data;

		const gripUpdate = applayGrid(canvas.ownerSVGElement, canvasData);

		function transform() {
			canvas.style.transform = `matrix(${canvasData.scale}, 0, 0, ${canvasData.scale}, ${canvasData.position.x}, ${canvasData.position.y})`;
			gripUpdate();
		}

		/**
		 * @param {number} nextScale
		 * @param {Point} originPoint
		 */
		function scale(nextScale, originPoint) {
			if (nextScale < 0.25 || nextScale > 4) { return; }

			const divis = nextScale / canvasData.scale;
			canvasData.scale = nextScale;

			canvasData.position.x = divis * (canvasData.position.x - originPoint.x) + originPoint.x;
			canvasData.position.y = divis * (canvasData.position.y - originPoint.y) + originPoint.y;

			transform();
		}

		// move, scale with fingers
		applayFingers(canvas.ownerSVGElement, canvasData, scale, transform);

		// scale with mouse wheel
		canvas.ownerSVGElement.addEventListener('wheel', /** @param {WheelEvent} evt */ evt => {
			evt.preventDefault();
			const delta = evt.deltaY || evt.deltaX;
			const scaleStep = Math.abs(delta) < 50
				? 0.05 // trackpad pitch
				: 0.25; // mouse wheel

			scale(
				canvasData.scale + (delta < 0 ? scaleStep : -scaleStep),
				evtPoint(evt));
		});

		canvas[CanvasSmbl].move = function (x, y, scale) {
			canvasData.position.x = x;
			canvasData.position.y = y;
			canvasData.scale = scale;
			transform();
		};
	}

	/**
	 * @param { SVGSVGElement } svg
	 * @param { {position:Point, scale:number} } canvasData
	 * @param { {(nextScale:number, originPoint:Point):void} } scaleFn
	 * @param { {():void} } transformFn
	 * @return
	 */
	function applayFingers(svg, canvasData, scaleFn, transformFn) {
		/** @type { Pointer } */
		let firstPointer;

		/** @type { Pointer} */
		let secondPointer;

		/** @type {number} */
		let distance;

		/** @type {Point} */
		let center;

		/** @param {PointerEvent} evt */
		function cancel(evt) {
			distance = null;
			center = null;
			if (firstPointer?.id === evt.pointerId) { firstPointer = null; }
			if (secondPointer?.id === evt.pointerId) { secondPointer = null; }

			if (!firstPointer && !secondPointer) {
				listenDel(svg, 'pointermove', move);
				listenDel(svg, 'pointercancel', cancel);
				listenDel(svg, 'pointerup', cancel);
			}
		}
		/** @param {PointerEvent} evt */
		function move(evt) {
			if (evt[ProcessedSmbl]) { return; }

			if ((firstPointer && !secondPointer) || (!firstPointer && secondPointer)) {
				// move with one pointer
				canvasData.position.x = evt.clientX + (firstPointer || secondPointer).shift.x;
				canvasData.position.y = evt.clientY + (firstPointer || secondPointer).shift.y;
				transformFn();
				return;
			}

			if (!secondPointer || !firstPointer || (secondPointer?.id !== evt.pointerId && firstPointer?.id !== evt.pointerId)) { return; }

			const distanceNew = Math.hypot(firstPointer.pos.x - secondPointer.pos.x, firstPointer.pos.y - secondPointer.pos.y);
			const centerNew = {
				x: (firstPointer.pos.x + secondPointer.pos.x) / 2,
				y: (firstPointer.pos.y + secondPointer.pos.y) / 2
			};

			// not first move
			if (distance) {
				canvasData.position.x = canvasData.position.x + centerNew.x - center.x;
				canvasData.position.y = canvasData.position.y + centerNew.y - center.y;

				scaleFn(
					canvasData.scale / distance * distanceNew,
					centerNew);
			}

			distance = distanceNew;
			center = centerNew;

			if (firstPointer.id === evt.pointerId) { firstPointer = evtPointer(evt, canvasData); }
			if (secondPointer.id === evt.pointerId) { secondPointer = evtPointer(evt, canvasData); }
		}

		listen(svg, 'pointerdown', /** @param {PointerEvent} evt */ evt => {
			if (evt[ProcessedSmbl] || (!firstPointer && !evt.isPrimary) || (firstPointer && secondPointer)) {
				return;
			}

			svg.setPointerCapture(evt.pointerId);
			if (!firstPointer) {
				listen(svg, 'pointermove', move);
				listen(svg, 'pointercancel', cancel);
				listen(svg, 'pointerup', cancel);
			}

			if (!firstPointer) { firstPointer = evtPointer(evt, canvasData); return; }
			if (!secondPointer) { secondPointer = evtPointer(evt, canvasData); }
		});
	}

	/**
	 * @param { SVGSVGElement } svg
	 * @param { import('./canvas-smbl.js').CanvasData } canvasData
	 */
	function applayGrid(svg, canvasData) {
		let curOpacity;
		/** @param {number} opacity */
		function backImg(opacity) {
			if (curOpacity !== opacity) {
				curOpacity = opacity;
				svg.style.backgroundImage = `radial-gradient(rgb(73 80 87 / ${opacity}) 1px, transparent 0)`;
			}
		}

		backImg(0.7);
		svg.style.backgroundSize = `${canvasData.cell}px ${canvasData.cell}px`;

		return function() {
			const size = canvasData.cell * canvasData.scale;

			if (canvasData.scale < 0.5) { backImg(0); } else
			if (canvasData.scale <= 0.9) { backImg(0.3); } else { backImg(0.7); }

			svg.style.backgroundSize = `${size}px ${size}px`;
			svg.style.backgroundPosition = `${canvasData.position.x}px ${canvasData.position.y}px`;
		};
	}

	/**
	 * @param {PointerEvent | MouseEvent} evt
	 * @return {Point}
	 */
	function evtPoint(evt) { return { x: evt.clientX, y: evt.clientY }; }

	/**
	 * @param { PointerEvent } evt
	 * @param { {position:Point, scale:number} } canvasData
	 * @return { Pointer }
	 */
	function evtPointer(evt, canvasData) {
		return {
			id: evt.pointerId,
			pos: evtPoint(evt),
			shift: {
				x: canvasData.position.x - evt.clientX,
				y: canvasData.position.y - evt.clientY
			}
		};
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { {id:number, pos:Point, shift:Point} } Pointer */
	/** @typedef { import("./move-evt-proc").ProcEvent } DgrmEvent */
	/** @typedef { import('./canvas-smbl.js').CanvasData } CanvasData */
	/** @typedef { import('./canvas-smbl.js').CanvasElement } CanvasElement */

	/** @param {Element} elem */
	function evtRouteApplay(elem) {
		elem.addEventListener('pointerdown', /** @param {RouteEvent} evt */ evt => {
			if (!evt.isPrimary || evt[RouteedSmbl] || !evt.isTrusted) { return; }

			evt.stopImmediatePropagation();

			const newEvt = new PointerEvent('pointerdown', evt);
			newEvt[RouteedSmbl] = true;
			activeElemFromPoint(evt).dispatchEvent(newEvt);
		}, { capture: true, passive: true });
	}

	/** @param { {clientX:number, clientY:number} } evt */
	function activeElemFromPoint(evt) {
		return elemFromPointByPrioity(evt).find(el => !el.hasAttribute('data-evt-no'));
	}

	/** @param { {clientX:number, clientY:number} } evt */
	function elemFromPointByPrioity(evt) {
		return document.elementsFromPoint(evt.clientX, evt.clientY)
			.sort((a, b) => {
				const ai = a.getAttribute('data-evt-index');
				const bi = b.getAttribute('data-evt-index');
				return (ai === bi) ? 0 : ai > bi ? -1 : 1;
			});
	}

	const RouteedSmbl = Symbol('routeed');
	/** @typedef {PointerEvent & { [RouteedSmbl]?: boolean }} RouteEvent */

	const PathSmbl = Symbol('path');
	/** @typedef {SVGGraphicsElement & { [PathSmbl]?: import("./path").Path }} PathElement */

	/** @param {CanvasElement} canvas */
	function canvasClear(canvas) {
		[...canvas.children].forEach(element => {
			let el = (element[ShapeSmbl] || element[PathSmbl]);
			if(el){  
				el.del();  // only delete it if it is a shape or a path
			}
		}); 
		canvas[CanvasSmbl].move(0, 0, 1);
	}

	//
	// selection clear function

	/** @param {CanvasElement} canvas */
	function canvasSelectionClear(canvas) {
		if (canvas[CanvasSmbl].selectClear) { canvas[CanvasSmbl].selectClear(); }}

	/** @param {CanvasElement} canvas, @param {()=>void} clearFn */
	function canvasSelectionClearSet(canvas, clearFn) {
		canvas[CanvasSmbl].selectClear = clearFn;
	}

	/** @typedef { import('../infrastructure/move-scale-applay.js').CanvasElement } CanvasElement */

	const v = '1.1';

	/** @param {Element} canvas */
	const serialize = (canvas) => serializeShapes(/** @type {Array<ShapeElement & PathElement>} */([...canvas.children]));

	/** @param {Array<ShapeElement & PathElement>} shapes */
	function serializeShapes(shapes) {
		/** @type {DiagramSerialized} */
		const diagramSerialized = { v, s: [] };
		for (const shape of shapes) {
			if (shape[ShapeSmbl]) {
				// shape
				diagramSerialized.s.push(shape[ShapeSmbl].data);
			} else if(shape[PathSmbl]) {
				// path
				/** @param {PathEnd} pathEnd */
				function pathSerialize(pathEnd) {
					const shapeIndex = shapes.indexOf(pathEnd.shape?.shapeEl);
					return (shapeIndex !== -1)
						? { s: shapeIndex, k: pathEnd.shape.connectorKey }
						: { p: pathEnd.data };
				}

				const pathData = shape[PathSmbl].data;
				const pathJson = { type: "line", s: pathSerialize(pathData.s), e: pathSerialize(pathData.e) };
				if (pathData.styles) { pathJson.c = pathData.styles; }
				if (pathData.sw) { pathJson.sw = pathData.sw; }
				if (pathData.sc) { pathJson.sc = pathData.sc; }

				diagramSerialized.s.push(pathJson);
			}
		}

		return diagramSerialized;
	}

	/**
	 * @param {CanvasElement} canvas
	 * @param {DiagramSerialized} data
	 * @param {Boolean=} dontClear
	 */
	function deserialize(canvas, data, dontClear) {
		if (data.v !== v) { alert('Wrong format'); return null; }
		if (!dontClear) { canvasClear(canvas); }

		/** @type {Map<ShapeData, ShapeElement>} */
		const shapeDataToElem = new Map();

		/** @param {ShapeData} shapeData */
		function shapeEnsure(shapeData) {
			let shapeEl = shapeDataToElem.get(shapeData);
			if (!shapeEl) {
				shapeEl = canvas[CanvasSmbl].shapeMap[shapeData.type].create(shapeData);
				canvas.append(shapeEl);
				shapeDataToElem.set(shapeData, shapeEl);
			}
			return shapeEl;
		}

		/** @param {number?} index */
		const shapeByIndex = index => shapeEnsure(/** @type {ShapeData} */(data.s[index]));

		/** @type {PathElement[]} */
		const paths = [];
		for (const shape of data.s) {
			switch (shape.type) {
				// path
				case "line": {
					/** @param {PathEndSerialized} pathEnd */
					const pathDeserialize = pathEnd => pathEnd.p
						? { data: pathEnd.p }
						: { shape: { shapeEl: shapeByIndex(pathEnd.s), connectorKey: pathEnd.k } };

					const path = canvas[CanvasSmbl].shapeMap["line"].create({
						styles: /** @type {PathSerialized} */(shape).c,
						s: pathDeserialize(/** @type {PathSerialized} */(shape).s),
						e: pathDeserialize(/** @type {PathSerialized} */(shape).e),
						sw: (shape).sw,
						sc: (shape).sc
					});
					paths.push(path);
					canvas.append(path);
					break;
				}
				default: shapeEnsure(/** @type {ShapeData} */(shape)); break;
			}
		}

		return [...shapeDataToElem.values(), ...paths];
	}

	/** @typedef {{v:string, s: Array<ShapeData | PathSerialized>}} DiagramSerialized */

	/** @typedef { import("../shapes/shape-smbl").ShapeElement } ShapeElement */
	/** @typedef { import('../shapes/shape-evt-proc').ShapeData } ShapeData */

	/** @typedef { import("../shapes/path-smbl").PathElement } PathElement */
	/** @typedef { import('../shapes/path').PathEndData } PathEndData */
	/** @typedef { import('../shapes/path').PathEnd } PathEnd */
	/** @typedef { import('../shapes/path').PathData } PathData */

	/** @typedef { {s?:number, k?:string, p?:PathEndData} } PathEndSerialized */
	/** @typedef { {type:string, c?:string, s:PathEndSerialized, e:PathEndSerialized} } PathSerialized */

	/** @typedef { import('../shapes/shape-evt-proc').CanvasData } CanvasData */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */

	/**
	 * @param {Blob} png
	 * @param {string} chunkName 4 symbol string
	 * @returns {Promise<DataView | null>} chunk data
	 */
	async function pngChunkGet(png, chunkName) {
		return chunkGet(
			await png.arrayBuffer(),
			toUit32(chunkName));
	}

	/**
	 * @param {Blob} png
	 * @param {string} chunkName 4 symbol string
	 * @param {Uint8Array} data
	 * @returns {Promise<Blob>} new png
	 */
	async function pngChunkSet(png, chunkName, data) {
		return chunkSet(
			await png.arrayBuffer(),
			toUit32(chunkName),
			data
		);
	}

	/**
	 * @param {ArrayBuffer} pngData
	 * @param {number} chunkNameUint32 chunk name as Uint32
	 * @param {Uint8Array} data
	 * @returns {Blob} new png
	 */
	function chunkSet(pngData, chunkNameUint32, data) {
		/** @type {DataView} */
		let startPart;
		/** @type {DataView} */
		let endPart;

		const existingChunk = chunkGet(pngData, chunkNameUint32);
		if (existingChunk) {
			startPart = new DataView(pngData, 0, existingChunk.byteOffset - 8);
			endPart = new DataView(pngData, existingChunk.byteOffset + existingChunk.byteLength + 4);
		} else {
			const endChunkStart = pngData.byteLength - 12; // 12 - end chunk length
			startPart = new DataView(pngData, 0, endChunkStart);
			endPart = new DataView(pngData, endChunkStart);
		}

		const chunkHeader = new DataView(new ArrayBuffer(8));
		chunkHeader.setUint32(0, data.length);
		chunkHeader.setUint32(4, chunkNameUint32);

		return new Blob([
			startPart,

			// new chunk
			chunkHeader,
			data,
			new Uint32Array([0]),	// CRC fake - not calculated

			endPart
		],
		{ type: 'image/png' });
	}

	/**
	 * @param {ArrayBuffer} pngData
	 * @param {number} chunkNameUint32 chunk name as Uint32
	 * @returns {DataView | null} chunk data
	 */
	function chunkGet(pngData, chunkNameUint32) {
		const dataView = new DataView(pngData, 8); // 8 byte - png signature

		let chunkPosition = 0;
		let chunkUint = dataView.getUint32(4);
		let chunkLenght;
		while (chunkUint !== 1229278788) { // last chunk 'IEND'
			chunkLenght = dataView.getUint32(chunkPosition);
			if (chunkUint === chunkNameUint32) {
				return new DataView(pngData, chunkPosition + 16, chunkLenght);
			}
			chunkPosition = chunkPosition + 12 + chunkLenght;
			chunkUint = dataView.getUint32(chunkPosition + 4);
		}
		return null;
	}

	/**
	 * @param {string} chunkName 4 symbol string
	 * @return {number} uit32
	 */
	function toUit32(chunkName) {
		return new DataView((new TextEncoder()).encode(chunkName).buffer).getUint32(0);
	}

	/* Convert cm to px */
	function getSizeInPX(sizeInCM) {
		const sizeInPX = (96 * sizeInCM) / 2.54;
		return sizeInPX;
	 }
	/**
	 * @param {SVGSVGElement} svg
	 * @param {{
			x: number;
	    	y: number;
			height: number;
	    	width: number;
		}} rect coordinates of the rect to export
	 * @param {number} imgWidth (in cm)
	 * @param {number} imgHeight (in cm)
	 * @param {BlobCallback} callBack
	 */
	function svgToPng(svg, rect, imgWidth, imgHeight, callBack) {
		const img = new Image();
		img.width = getSizeInPX(imgWidth);
		img.height = getSizeInPX(imgHeight);
		img.onload = function() {
			const canvas = document.createElement('canvas');
			canvas.width = img.width;
			canvas.height = img.height;
			canvas.style.width = `${img.width}px`;
			canvas.style.height = `${img.height}px`;

			const ctx = canvas.getContext('2d');
			ctx.imageSmoothingEnabled = false;
			ctx.drawImage(
				img,
				rect.x, // sx
				rect.y, // sy
				img.width, // sWidth
				img.height, // sHeight

				0,	// dx
				0,	// dy
				img.width, // dWidth
				img.height // dHeight
			);
			URL.revokeObjectURL(img.src);

			canvas.toBlob(callBack, 'image/png');
		};
		
		svg.setAttribute("viewBox", `0 0 ${rect.width} ${rect.height}`);
		svg.width.baseVal.newValueSpecifiedUnits(SVGLength.SVG_LENGTHTYPE_PX, img.width);
		svg.height.baseVal.newValueSpecifiedUnits(SVGLength.SVG_LENGTHTYPE_PX, img.height);
		img.src = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)], { type: 'image/svg+xml;charset=utf-8' }));
	}

	/**
	 * @param {CanvasElement} canvas
	 * @param {string} dgrmChunkVal
	 * @param {number} imgWidth (in cm)
	 * @param {number} imgHeight (in cm)
	 * @param {BlobCallback} callBack
	 */
	function dgrmPngCreate(canvas, dgrmChunkVal, imgWidth, imgHeight, callBack) {
		const rectToShow = canvas.getBoundingClientRect();
		const svgVirtual = /** @type {SVGSVGElement} */(canvas.ownerSVGElement.cloneNode(true));
		svgVirtual.style.backgroundImage = null;
		svgVirtual.querySelectorAll('.select').forEach(el => el.classList.remove('select'));

		const nonSvgElems = svgVirtual.getElementsByTagName('foreignObject');
		while (nonSvgElems[0]) { nonSvgElems[0].parentNode.removeChild(nonSvgElems[0]); }

		const canvasData = canvas[CanvasSmbl].data;

		// diagram to left corner
		const canvasElVirtual = /** @type{SVGGraphicsElement} */(svgVirtual.children[1]);
		const divis = 1 / canvasData.scale;
		canvasElVirtual.style.transform = `matrix(1, 0, 0, 1, ${divis * (canvasData.position.x + 15 * canvasData.scale - rectToShow.x)}, ${divis * (canvasData.position.y + 15 * canvasData.scale - rectToShow.y)})`;

		svgToPng(svgVirtual,
			{ x: 0, y: 0, height: rectToShow.height / canvasData.scale + 30, width: rectToShow.width / canvasData.scale + 30 },
			// size of the image: width and height in centimeters
			imgWidth, imgHeight,
			// callBack
			async blob => callBack(await pngChunkSet(blob, 'dgRm', new TextEncoder().encode(dgrmChunkVal)))
		);
	}

	/**
	 * @param {Blob} png
	 * @returns {Promise<string|null>}
	 */
	async function dgrmPngChunkGet(png) {
		const dgrmChunkVal = await pngChunkGet(png, 'dgRm');
		return dgrmChunkVal ? new TextDecoder().decode(dgrmChunkVal) : null;
	}

	const blobToBase64 = blob => new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.readAsDataURL(blob);
		reader.onload = () => resolve(reader.result);
		reader.onerror = error => reject(error);
		});

	const convertBlobToBase64 = async (blob) => { // blob data
		return await blobToBase64(blob);
	};
	  



	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */

	function registerExternalEvents(canvas){
	    const event = new Event("serializeall");
	    const loadjson = new Event("loadjson");
	    const savepng = new Event("savepng");
	    canvas.dispatchEvent(event);
	    canvas.dispatchEvent(loadjson);
	    canvas.dispatchEvent(savepng);
	    canvas.addEventListener(
	        "serializeall",
	        (e) => {
	          let itemid = e.detail;
	          itemid.value=JSON.stringify(serializeShapes([...canvas.children]));
	        },
	        false
	      );
	    canvas.addEventListener(
	        "loadjson",
	        (e) => {
	          let data = e.detail.data;
	          deserialize(canvas, data, e.detail.dontClear);
	        },
	        false
	    );


	    canvas.addEventListener(
	      "savepng",
	      (e) => {
	        let callback = e.detail.callback;
	        const serialized = serialize(canvas);
	        if (serialized.s.length === 0) {  return; }
	        dgrmPngCreate(
	          canvas,
	          JSON.stringify(serialized),
	          e.detail.width, e.detail.height,  // img size (width, height) in centimeters
	          png =>   {
	             convertBlobToBase64(png).then(callback);
	          } );
	      },
	      false
	  );






	}

	const delSvg = '<svg data-cmd="del" data-cmd-type="click" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M17 6h5v2h-2v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V8H2V6h5V3a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v3zm1 2H6v12h12V8zm-9 3h2v6H9v-6zm4 0h2v6h-2v-6zM9 4v2h6V4H9z" fill="rgb(52,71,103)"/></svg>';
	const copySvg = '<svg data-cmd="copy" data-cmd-type="click" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M7 6V3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-3v3c0 .552-.45 1-1.007 1H4.007A1.001 1.001 0 0 1 3 21l.003-14c0-.552.45-1 1.007-1H7zM5.003 8L5 20h10V8H5.003zM9 6h8v10h2V4H9v2z" fill="rgb(52,71,103)"/></svg>';

	class GroupSettings extends HTMLElement {
		/** @param {(cms:string)=>void} cmdHandler */
		constructor(cmdHandler) {
			super();
			/** @private */
			this._cmdHandler = cmdHandler;
		}

		connectedCallback() {
			const shadow = this.attachShadow({ mode: 'closed' });
			shadow.innerHTML = `
		<style>
			.ln { display: flex; }
			.ln > * {
				height: 24px;
				padding: 10px;
			}
			[data-cmd] { cursor: pointer; }
		</style>
		<div class="ln">
			${copySvg}
			${delSvg}
		</div>`;

			clickForAll(shadow, '[data-cmd]',
				evt => this._cmdHandler(evtTargetAttr(evt, 'data-cmd')));
		}
	}
	customElements.define('ap-grp-settings', GroupSettings);

	/** @type {HTMLDivElement} */
	let editModalDiv;
	/** @param {number} bottomX, @param {number} bottomY, @param {HTMLElement} elem */
	function modalCreate(bottomX, bottomY, elem) {
		editModalDiv = document.createElement('div');
		editModalDiv.style.cssText = 'position: fixed; box-shadow: 0px 0px 58px 2px rgb(34 60 80 / 20%); border-radius: 16px; background-color: rgba(255,255,255, .9);';
		editModalDiv.append(elem);
		document.body.append(editModalDiv);

		function position(btmX, btmY) {
			editModalDiv.style.left = `${btmX}px`;
			editModalDiv.style.top = `${window.scrollY + btmY - editModalDiv.getBoundingClientRect().height}px`; // window.scrollY fix IPhone keyboard
		}
		position(bottomX, bottomY);

		return {
			/**
			 * @param {number} bottomX positon of the bottom left corner of the panel
			 * @param {number} bottomY positon of the bottom left corner of the panel
			 */
			position,
			del: () => { editModalDiv.remove(); editModalDiv = null; }
		};
	}

	/** @param {number} dif */
	function modalChangeTop(dif) {
		editModalDiv.style.top = `${editModalDiv.getBoundingClientRect().top + dif}px`;
	}

	/** @param {CanvasElement} canvas, @param {DiagramSerialized} data */
	function groupMoveToCenter(canvas, data) {
		const screenCenter = pointInCanvas(canvas[CanvasSmbl].data, window.innerWidth / 2, window.innerHeight / 2);
		placeToCell(screenCenter, canvas[CanvasSmbl].data.cell);

		const shift = pointShift(screenCenter, centerCalc(data), -1);
		iteratePoints(data, point => { if (point) { pointShift(point, shift); } });
	}

	/** @param {DiagramSerialized} data */
	function centerCalc(data) {
		const minMax = maxAndMinPoint(data);
		return {
			x: minMax.min.x + (minMax.max.x - minMax.min.x) / 2,
			y: minMax.min.y + (minMax.max.y - minMax.min.y) / 2
		};
	}

	/** @param {DiagramSerialized} data */
	function maxAndMinPoint(data) {
		/** @type {Point} */
		const min = { x: Infinity, y: Infinity };

		/** @type {Point} */
		const max = { x: -Infinity, y: -Infinity };

		iteratePoints(data, point => {
			if (!point) { return; }

			if (min.x > point.x) { min.x = point.x; }
			if (min.y > point.y) { min.y = point.y; }

			if (max.x < point.x) { max.x = point.x; }
			if (max.y < point.y) { max.y = point.y; }
		});
		return { min, max };
	}

	/** @param {DiagramSerialized} data, @param {(point:Point)=>void} callbackfn */
	function iteratePoints(data, callbackfn) {
		data.s.forEach(shapeOrPath => {
			if (shapeOrPath.type === "line") {
				// path
				callbackfn(/** @type {PathSerialized} */(shapeOrPath).s.p?.position);
				callbackfn(/** @type {PathSerialized} */(shapeOrPath).e.p?.position);
			} else {
				// shape
				callbackfn(/** @type {ShapeData} */(shapeOrPath).position);
			}
		});
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('./dgrm-serialization.js').DiagramSerialized } DiagramSerialized */
	/** @typedef { import('./dgrm-serialization.js').PathSerialized } PathSerialized */
	/** @typedef { import('../shapes/shape-evt-proc.js').ShapeData } ShapeData */

	//
	// copy past

	const clipboardDataKey = 'dgrm';

	/** @param {() => Array<ShapeElement & PathElement>} shapesToClipboardGetter */
	function listenCopy(shapesToClipboardGetter) {
		/** @param {ClipboardEvent & {target:HTMLElement | SVGElement}} evt */
		function onCopy(evt) {
			const shapes = shapesToClipboardGetter();
			if (document.activeElement === shapes[0].ownerSVGElement) {
				evt.preventDefault();
				evt.clipboardData.setData(
					clipboardDataKey,
					JSON.stringify(copyDataCreate(shapes)));
			}
		}
		document.addEventListener('copy', onCopy);

		// dispose fn
		return function() {
			listenDel(document, 'copy', onCopy);
		};
	}

	/** @param {CanvasElement} canvas */
	function copyPastApplay(canvas) {
		listen(document, 'paste', /** @param {ClipboardEvent & {target:HTMLElement | SVGElement}} evt */ evt => {
			if (evt.target.tagName.toUpperCase() === 'TEXTAREA') { return; }
			// if (document.activeElement !== canvas.ownerSVGElement) { return; }

			const dataStr = evt.clipboardData.getData(clipboardDataKey);
			if (!dataStr) { return; }

			canvasSelectionClear(canvas);
			past(canvas, JSON.parse(dataStr));
		});
	}

	/** @param {CanvasElement} canvas, @param {Array<ShapeElement & PathElement>} shapes */
	const copyAndPast = (canvas, shapes) => past(canvas, copyDataCreate(shapes));

	/** @param {Array<ShapeElement & PathElement>} shapes */
	const copyDataCreate = shapes => deepCopy(serializeShapes(shapes));

	/** @param {CanvasElement} canvas, @param {DiagramSerialized} data */
	function past(canvas, data) {
		canvasSelectionClear(canvas);
		groupMoveToCenter(canvas, data);
		groupSelect(canvas, deserialize(canvas, data, true));
	}

	//
	// group select

	const highlightClass = 'select';

	/** wait long press and draw selected rectangle
	 * @param {CanvasElement} canvas
	 */
	function groupSelectApplay(canvas) {
		const svg = canvas.ownerSVGElement;
		let timer;
		/** @type {Point} */ let selectStart;
		/** @type {SVGCircleElement} */ let startCircle;
		/** @type {SVGRectElement} */ let selectRect;
		/** @type {Point} */ let selectRectPos;

		/** @param {PointerEvent} evt */
		function onMove(evt) {
			if (evt[ProcessedSmbl] || !selectRect) { reset(); return; }
			evt[ProcessedSmbl] = true;

			if (startCircle) { startCircle.remove(); startCircle = null; }

			// draw rect
			const x = evt.clientX - selectStart.x;
			const y = evt.clientY - selectStart.y;
			selectRect.width.baseVal.value = Math.abs(x);
			selectRect.height.baseVal.value = Math.abs(y);
			if (x < 0) { selectRectPos.x = evt.clientX; }
			if (y < 0) { selectRectPos.y = evt.clientY; }
			selectRect.style.transform = `translate(${selectRectPos.x}px, ${selectRectPos.y}px)`;
		}

		function onUp() {
			if (selectRect) {
				/** @param {Point} point */
				const inRect = point => pointInRect(
					pointInCanvas(canvas[CanvasSmbl].data, selectRectPos.x, selectRectPos.y),
					selectRect.width.baseVal.value / canvas[CanvasSmbl].data.scale,
					selectRect.height.baseVal.value / canvas[CanvasSmbl].data.scale,
					point.x, point.y);

				// select shapes in rect
				groupSelect(
					canvas,
					/** @type {Iterable<ShapeOrPathElement>} */(canvas.children),
					inRect);
			}

			reset();
		}

		function reset() {
			clearTimeout(timer); timer = null;
			startCircle?.remove(); startCircle = null;
			selectRect?.remove(); selectRect = null;

			listenDel(svg, 'pointermove', onMove);
			listenDel(svg, 'wheel', reset);
			listenDel(svg, 'pointerup', onUp);
		}

		listen(svg, 'pointerdown', /** @param {PointerEvent} evt */ evt => {
			if (evt[ProcessedSmbl] || !evt.isPrimary) { reset(); return; }

			listen(svg, 'pointermove', onMove);
			listen(svg, 'wheel', reset, true);
			listen(svg, 'pointerup', onUp, true);

			timer = setTimeout(_ => {
				canvasSelectionClear(canvas);

				startCircle = svgEl('circle');
				classAdd(startCircle, 'ative-elem');
				startCircle.style.cssText = 'r:10px; fill: rgb(108 187 247 / 51%)';
				positionSet(startCircle, { x: evt.clientX, y: evt.clientY });
				svg.append(startCircle);

				selectStart = { x: evt.clientX, y: evt.clientY };
				selectRectPos = { x: evt.clientX, y: evt.clientY };
				selectRect = svgEl('rect');
				selectRect.style.cssText = 'rx:10px; fill: rgb(108 187 247 / 51%)';
				positionSet(selectRect, selectRectPos);
				svg.append(selectRect);
			}, 500);
		});
	}

	/**
	 * Highlight selected shapes and procces group operations (move, del, copy)
	 * @param {CanvasElement} canvas
	 * @param {Iterable<ShapeOrPathElement>} elems
	 * @param {{(position:Point):boolean}=} inRect
	 */
	function groupSelect(canvas, elems, inRect) {
		/** @param {{position:Point}} data */
		const shapeInRect = data => inRect ? inRect(data.position) : true;

		/** @type {Selected} */
		const selected = {
			shapes: [],
			shapesPaths: [],
		};

		for (const shapeEl of elems) {
			if (shapeEl[ShapeSmbl]) {
				if (shapeInRect(shapeEl[ShapeSmbl].data)) {
					classAdd(shapeEl, highlightClass);
					selected.shapes.push(shapeEl);
				}
			} else if (shapeEl[PathSmbl]) {
				if(shapeInRect(shapeEl[PathSmbl].data.s.data) && shapeInRect(shapeEl[PathSmbl].data.e.data)){
					classAdd(shapeEl, highlightClass);
					selected.shapesPaths.push(shapeEl);
				}
			}
		}

		groupEvtProc(canvas, selected);
	}

	/**
	 * @param {CanvasElement} canvas
	 * @param {Selected} selected
	 */
	function groupEvtProc(canvas, selected) {
		// only one shape selected
		if (selected.shapes?.length === 1 && !selected.shapesPaths?.length) {
			classDel(selected.shapes[0], 'select');
			shapeSelect(selected.shapes[0]);
			return;
		}

		// only one path selected
		if (!selected.shapes?.length && selected.shapesPaths?.length == 1) {
			classDel(selected.shapesPaths[0], 'select');
			shapeSelect(selected.shapesPaths[0]);
			return;
		}

		const svg = canvas.ownerSVGElement;
		let isMove = false;
		let isDownOnSelectedShape = false;

		/** @type {{del():void}} */
		let settingsPnl;
		const pnlDel = () => { settingsPnl?.del(); settingsPnl = null; };

		/** @param {PointerEvent & {target:Node}} evt */
		function down(evt) {
			pnlDel();
			isDownOnSelectedShape =
				selected.shapes?.some(shapeEl => shapeEl.contains(evt.target)) ||
				selected.shapesPaths?.some(pathEl => pathEl.contains(evt.target));


			// down on not selected shape
			if (!isDownOnSelectedShape && evt.target !== svg) {
				dispose();
				return;
			}

			if (isDownOnSelectedShape) {
				evt.stopImmediatePropagation();
			}

			svg.setPointerCapture(evt.pointerId);
			listen(svg, 'pointerup', up, true);
			listen(svg, 'pointermove', move);
		}

		/** @param { {(point:Point):void} } pointMoveFn */
		function drawSelection(pointMoveFn) {
			selected.shapes?.forEach(shapeEl => {
				pointMoveFn(shapeEl[ShapeSmbl].data.position);
				shapeEl[ShapeSmbl].drawPosition();
			});
			selected.shapesPaths?.forEach(pathEl => {
				pointMoveFn(pathEl[PathSmbl].data.e.data.position);
				pointMoveFn(pathEl[PathSmbl].data.s.data.position);
				pathEl[PathSmbl].draw();
			});
		}

		/** @param {PointerEvent} evt */
		function up(evt) {
			if (!isMove) {
				// click on canvas
				if (!isDownOnSelectedShape) { dispose(); return; }

				// click on selected shape - show settings panel
				settingsPnl = modalCreate(evt.clientX - 10, evt.clientY - 10, new GroupSettings(cmd => {
					switch (cmd) {
						case 'del':
							arrPop(selected.shapes, shapeEl => shapeEl[ShapeSmbl].del());
							arrPop(selected.shapesPaths, pathEl => pathEl[PathSmbl].del());
							dispose();
							break;
						case 'copy': {
							copyAndPast(canvas, elemsToCopyGet(selected)); // will call dispose
							break;
						}
					}
				}));
			} else {
				// move end
				drawSelection(point => placeToCell(point, canvas[CanvasSmbl].data.cell));
			}

			dispose(true);
		}

		/** @param {PointerEventFixMovement} evt */
		function move(evt) {
			// move canvas
			if (!isDownOnSelectedShape) { dispose(true); return; }

			// move selected shapes
			isMove = true;
			drawSelection(point => movementApplay(point, canvas[CanvasSmbl].data.scale, evt));
		}

		/** @param {boolean=} saveOnDown */
		function dispose(saveOnDown) {
			listenDel(svg, 'pointerup', up);
			listenDel(svg, 'pointermove', move);
			isMove = false;
			isDownOnSelectedShape = false;

			if (!saveOnDown) {
				canvasSelectionClearSet(canvas, null);
				if (listenCopyDispose) { listenCopyDispose(); listenCopyDispose = null; }

				listenDel(svg, 'pointerdown', down, true);
				pnlDel();
				arrPop(selected.shapes, shapeEl => classDel(shapeEl, highlightClass));
				arrPop(selected.shapesPaths, pathEl => classDel(pathEl, highlightClass));
				selected.shapesPaths = null;
				selected.shapes = null;
			}
		}

		svg.addEventListener('pointerdown', down, { passive: true, capture: true });

		canvasSelectionClearSet(canvas, dispose);
		let listenCopyDispose = listenCopy(() => elemsToCopyGet(selected));
	}

	/** @param {Selected} selected */
	function elemsToCopyGet(selected) {
		/** @type {Set<PathElement>} */
		const fullSelectedPaths = new Set();

		/** @param {PathElement} pathEl */
		function fullSelectedPathAdd(pathEl) {
			fullSelectedPaths.add(pathEl);
		}

		selected.shapesPaths?.forEach(fullSelectedPathAdd);

		return [...selected.shapes, ...fullSelectedPaths];
	}

	/**
	 * @param {Point} rectPosition
	 * @param {number} rectWidth, @param {number} rectHeight
	 * @param {number} x, @param {number} y
	 */
	const pointInRect = (rectPosition, rectWidth, rectHeight, x, y) =>
		rectPosition.x <= x && x <= rectPosition.x + rectWidth &&
		rectPosition.y <= y && y <= rectPosition.y + rectHeight;

	/**
	 * @typedef { {
	 * 	shapes:ShapeElement[]
	 * 	shapesPaths:PathElement[]
	 * } } Selected
	 */
	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('../shapes/shape-smbl').ShapeElement } ShapeElement */
	/** @typedef { import('../shapes/shape-evt-proc').Shape } Shape */
	/** @typedef { import('../shapes/path').Path } Path */
	/** @typedef { import('../shapes/path-smbl').PathElement } PathElement */
	/** @typedef { SVGGraphicsElement & { [ShapeSmbl]?: Shape, [PathSmbl]?:Path }} ShapeOrPathElement */
	/** @typedef { import('../infrastructure/move-evt-mobile-fix.js').PointerEventFixMovement} PointerEventFixMovement */
	/** @typedef { import('./dgrm-serialization.js').DiagramSerialized } DiagramSerialized */

	/**
	 * @param {SVGTextElement} textEl target text element
	 * @param {number} verticalMiddle
	 * @param {string} str
	 * @returns {void}
	 */
	function svgTextDraw(textEl, verticalMiddle, str) {
		const strData = svgStrToTspan(
			(str || ''),
			textEl.x?.baseVal[0]?.value ?? 0);

		textEl.innerHTML = strData.s;

		textEl.y.baseVal[0].newValueSpecifiedUnits(
			textEl.y.baseVal[0].SVG_LENGTHTYPE_EMS, // em
			strData.c > 0 ? verticalMiddle - (strData.c) / 2 : verticalMiddle);
	}

	/**
	 * create multiline tspan markup
	 * @param {string} str
	 * @param {number} x
	 * @returns { {s:string, c:number} }
	 */
	function svgStrToTspan(str, x) {
		let c = 0;
		return {
			s: str.split('\n')
				.map((t, i) => {
					c = i;
					return `<tspan x="${x}" dy="${i === 0 ? 0.41 : 1}em" ${t.length === 0 ? 'visibility="hidden"' : ''}>${t.length === 0 ? '.' : escapeHtml(t).replaceAll(' ', '&nbsp;')}</tspan>`;
				}).join(''),
			c
		};
	}

	/**
	 * @param {string} str
	 * @returns {string}
	 */
	function escapeHtml(str) {
		return str.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;');
	}

	/**
	 * Create teaxtArea above SVGTextElement 'textEl'
	 * update 'textEl' with text from teaxtArea
	 * resize teaxtArea - so teaxtArea always cover all 'textEl'
	 * @param {SVGTextElement} textEl
	 * @param {number} verticalMiddle em
	 * @param {string} val
	 * @param {{(val:string):void}} onchange
	 * @param {{(val:string):void}} onblur
	 */
	function textareaCreate(textEl, verticalMiddle, val, onchange, onblur) {
		let foreign = svgEl('foreignObject');
		const textarea = document.createElement('textarea');
		const draw = () => foreignWidthSet(textEl, foreign, textarea, textareaPaddingAndBorder, textareaStyle.textAlign);

		textarea.value = val || '';
		textarea.setAttribute('data-key', 'textarea');
		textarea.oninput = function() {
			svgTextDraw(textEl, verticalMiddle, textarea.value);
			onchange(textarea.value);
			draw();
		};
		textarea.onblur = function() {
			onblur(textarea.value);
		};
		textarea.onpointerdown = function(evt) {
			evt.stopImmediatePropagation();
		};

		foreign.appendChild(textarea);
		textEl.parentElement.appendChild(foreign);

		const textareaStyle = getComputedStyle(textarea);
		// must be in px
		const textareaPaddingAndBorder = parseInt(textareaStyle.paddingLeft) + parseInt(textareaStyle.borderWidth);
		draw();

		textarea.focus();

		return {
			dispose: () => { foreign.remove(); foreign = null; },
			draw
		};
	}

	/**
	 * @param {SVGTextElement} textEl
	 * @param {SVGForeignObjectElement} foreign
	 * @param {HTMLTextAreaElement} textarea
	 * @param {number} textareaPaddingAndBorder
	 * @param {string} textAlign
	 */
	function foreignWidthSet(textEl, foreign, textarea, textareaPaddingAndBorder, textAlign) {
		const textBbox = textEl.getBBox();
		const width = textBbox.width + 20; // +20 paddings for iPhone

		foreign.width.baseVal.value = width + 2 * textareaPaddingAndBorder + 2; // +2 magic number for FireFox
		foreign.x.baseVal.value = textBbox.x - textareaPaddingAndBorder - (
			textAlign === 'center'
				? 10
				: textAlign === 'right' ? 20 : 0);

		foreign.height.baseVal.value = textBbox.height + 2 * textareaPaddingAndBorder + 3; // +3 magic number for FireFox
		foreign.y.baseVal.value = textBbox.y - textareaPaddingAndBorder;
		
		textarea.style.width = `${width}px`;
		textarea.style.height = `${textBbox.height}px`;
		textarea.style.fontSize = textEl.style.fontSize;
		textarea.style.fontFamily = textEl.style.fontFamily;
	}

	var pictogram_url_path ="";
	const pictogramSVGImages = [
	    { name: "sga-acid", filepath: "sga/acid.svg" },
	    { name: "sga-aquatic-pollution", filepath: "sga/aquatic-pollution.svg" },
	    { name: "sga-bottle", filepath: "sga/bottle.svg" },
	    { name: "sga-exclamation", filepath: "sga/exclamation.svg" },
	    { name: "sga-explosion", filepath: "sga/explosion.svg" },
	    { name: "sga-flammable-gas", filepath: "sga/flammable-gas.svg" },
	    { name: "sga-round-flame", filepath: "sga/round-flame.svg" },
	    { name: "sga-silhouete", filepath: "sga/silhouete.svg" },
	    { name: "sga-skull", filepath: "sga/skull.svg" },
	    { name: "un-acid8", filepath: "united_nations/acid8.svg" },
	    { name: "un-aquatic-pollution", filepath: "united_nations/aquatic-pollution.svg" },
	    { name: "un-blue4", filepath: "united_nations/blue4.svg" },
	    { name: "un-explosives1", filepath: "united_nations/explosives1.svg" },
	    { name: "un-explosives1-1", filepath: "united_nations/explosives1-1.svg" },
	    { name: "un-explosives1-2", filepath: "united_nations/explosives1-2.svg" },
	    { name: "un-explosives1-3", filepath: "united_nations/explosives1-3.svg" },
	    { name: "un-explosives1-4", filepath: "united_nations/explosives1-4.svg" },
	    { name: "un-explosives1-5", filepath: "united_nations/explosives1-5.svg" },
	    { name: "un-explosives1-6", filepath: "united_nations/explosives1-6.svg" },
	    { name: "un-green2", filepath: "united_nations/green2.svg" },
	    { name: "un-red2", filepath: "united_nations/red2.svg" },
	    { name: "un-red3", filepath: "united_nations/red3.svg" },
	    { name: "un-red-white4", filepath: "united_nations/red-white4.svg" },
	    { name: "un-skull2", filepath: "united_nations/skull2.svg" },
	    { name: "un-skull6", filepath: "united_nations/skull6.svg" },
	    { name: "un-stripes4", filepath: "united_nations/stripes4.svg" },
	    { name: "un-yellow5-1", filepath: "united_nations/yellow5-1.svg" },
	    { name: "un-yellow-red5-2", filepath: "united_nations/yellow-red5-2.svg" },
	];

	function readSVGAndGetDataURL(filename){
	    let request = new XMLHttpRequest();
	    request.open('get', filename, false); 
	    request.send(null);
	    return btoa(decodeURIComponent(encodeURIComponent(request.responseText)));
	}

	function getPictogramUrl(filepath){
	    let obj = pictogramSVGImages.find(o => o.filepath === filepath);
	    if(obj === undefined){
	        let  b64Data = readSVGAndGetDataURL(pictogram_url_path + filepath);
	        obj = {
	            name: filepath,
	            filepath: filepath,
	            b64Data: b64Data
	        };
	        pictogramSVGImages.push(obj);
	    }
	    return `data:image/svg+xml;base64,${obj.b64Data}`;
	}

	function getPictogramPatternsHtml(){
	    let patternsHtml = '';
	    let b64Data = '';
	    pictogramSVGImages.forEach(pattern => {
	        b64Data = readSVGAndGetDataURL(pictogram_url_path + pattern.filepath);
	        pattern.b64Data = b64Data;
	        patternsHtml += `<pattern id="${pattern.name}" x="0" y="0" width="1" height="1" viewBox="0 0 75 75"><image x="0" y="0" width="75" height="75" href="data:image/svg+xml;base64,${b64Data}"></image></pattern>`;
	    });
	    return patternsHtml;
	}

	function addPictogramPatterns(canvas, pictogram_path){
	    pictogram_url_path = pictogram_path;
	    let defsEl = child(canvas, "pictogram-patterns");
	    defsEl.innerHTML = getPictogramPatternsHtml();
	}

	/**
	 * @param {import('../infrastructure/canvas-smbl').CanvasElement} canvas
	 * @param {import('./shape-smbl').ShapeElement} shapeElement
	 * @param {number} bottomX positon of the bottom left corner of the panel
	 * @param {number} bottomY positon of the bottom left corner of the panel
	 */
	function settingsPnlCreate(canvas, shapeElement, bottomX, bottomY) {
		const shapeSettings = new ShapeEdit(shapeElement);

		listen(shapeSettings, 'cmd', /** @param {CustomEvent<{cmd:string, arg:string, extra:Object}>} evt */ evt => {
			switch (evt.detail.cmd) {
				case 'element-color': applyElementColor(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg, "shape"); break;
				case 'del': shapeElement[ShapeSmbl].del(); break;
				case 'copy': copyAndPast(canvas, [shapeElement]); break;
				case 'txt-align': textAlign(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.extra.alignEl, /** @type {1|2|3} */(Number.parseInt(evt.detail.arg))); break;
				case 'font-family': applyFontFamily(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg); break;
				case 'font-size': applyFontSize(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg); break;
				case 'font-color': applyFontColor(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg); break;
				case 'border-color': applyBorderColor(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg); break;
				case 'border-width': applyBorderWidth(shapeElement, shapeElement[ShapeSmbl].data, Number.parseFloat(evt.detail.arg)); break;
				case 'arrange': arrangeElement(shapeElement, evt.detail.arg); break;
				case 'txt-style': applyTxtStyle(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg, evt.detail.extra.txtStyleEl); break;
				case 'pictogram': setPictogram(shapeElement, shapeElement[ShapeSmbl].data, evt.detail.arg, evt.detail.extra.pictogramSelectEl); break;
			}
		});
		return modalCreate(bottomX, bottomY, shapeSettings);
	}

	class ShapeEdit extends HTMLElement {
		/**
		 * @param {import('./shape-smbl').ShapeElement} shapeElement
		 */

		constructor(shapeElement) {
			super();

			/** @private */
			this._shapeElement = shapeElement;

			/** @private */
			this._shapeData = undefined;
			if(this._shapeElement !== undefined){
				this._shapeData = this._shapeElement[ShapeSmbl].data;
			}
		}

		connectedCallback() {
			const shadow = this.attachShadow({ mode: 'open' });
			shadow.innerHTML =
			`<style>
			.ln, 
			.section { 
				display: flex; 
			}

			.ln > * {
				height: 24px;
				padding: 10px;
				cursor: pointer;
			}

			.align .ln > *, 
			.txt-style .ln > * {
				fill-opacity: 0.3;
				stroke-opacity: 0.3;
			}

			#prop { padding-bottom: 10px; }

			.ta-1 [data-cmd-arg="1"],
			.ta-2 [data-cmd-arg="2"],
			.ta-3 [data-cmd-arg="3"]
			{ fill-opacity: 1; stroke-opacity: 1; }

			.ts-bold [data-cmd-arg="bold"], 
			.ts-italic [data-cmd-arg="italic"], 
			.ts-underline [data-cmd-arg="underline"] {
				 fill-opacity: 1; stroke-opacity: 1; 
			}

			.form-div {
				padding: 10px;
			}

			.form-div > * {
				font-size: 12px;
			}

			select {
				padding: 5px;
				cursor: pointer;
				border-radius: 8px;
				width: 55%;
				background: none;
			}

			label {
				display: inline-block;
				font-weight: bold;
				width: 35%;
			}

			input {
				width: 55%;
			}
		
			img {
				max-height: 60px;
				padding: 0.5px;
				cursor: pointer;
			}

			.pictograms-select div.pictogram:not(.selected) {
				display: none;
			}

			.pictograms-select div.pictogram.selected {
				display: block;
			}

			.pictograms-select label {
				display: inline;
			}

			.pictograms-select:hover div.pictogram {
				display:block;
			}

			.title {
				text-align: center;
				font-size: 14px;
				font-weight: bold;
				margin-bottom: 0;
			}
		</style>
		<div id="pnl">
			<div id="color" style="display: none;">
				<div class="form-div">
					<label for="element-color">Element Color:</label>
					<input type="color" id="element-color" data-cmd="element-color" data-cmd-type="change">
				</div>
			</div>
			<div id="align" class="align" style="display: none;">
				<div class="ln">
					<div style="margin-left: ${this._shapeData && !this._shapeData.t ? '67px' : '23px'}"></div>
					<svg data-cmd="txt-align" data-cmd-type="click" data-cmd-arg="1" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 4h18v2H3V4zm0 15h14v2H3v-2zm0-5h18v2H3v-2zm0-5h14v2H3V9z" fill="rgb(52,71,103)"/></svg>
					<svg data-cmd="txt-align" data-cmd-type="click" data-cmd-arg="2" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 4h18v2H3V4zm2 15h14v2H5v-2zm-2-5h18v2H3v-2zm2-5h14v2H5V9z" fill="rgb(52,71,103)"/></svg>
					<svg data-cmd="txt-align" data-cmd-type="click" data-cmd-arg="3" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 4h18v2H3V4zm4 15h14v2H7v-2zm-4-5h18v2H3v-2zm4-5h14v2H7V9z" fill="rgb(52,71,103)"/></svg>
				</div>
			</div>
			<div id="font" class="font" style="display: none;">
				<div class="form-div">
					<label for="font-family">Font Family:</label>
					<select name="font-family" id="font-family" data-cmd="font-family" data-cmd-type="change">
						<option value="Arial" style="font-family:Arial;">Arial</option>
						<option value="Carlito" style="font-family: Carlito;">Carlito</option>
						<option value="Cousine" style="font-family: Cousine;">Cousine</option>
						<option value="Dejavu Sans" style="font-family: Dejavu Sans;">Dejavu Sans</option>
						<option value="Mono" style="font-family: Mono;">Mono</option>
						<option value="Paciencia" style="font-family: Paciencia;">Paciencia</option>
					</select>
				</div>
				<div class="form-div">
					<label for="font-size">Font Size:</label>
					<select name="font-size" id="font-size" data-cmd="font-size" data-cmd-type="change">
						<option value="12px">12</option>
						<option value="14px">14</option>
						<option value="16px">16</option>
						<option value="18px">18</option>
						<option value="20px">20</option>
						<option value="30px">30</option>
						<option value="40px">40</option>
						<option value="60px">60</option>
						<option value="80px">80</option>
						<option value="100px">100</option>
					</select>
				</div>
				<div class="form-div">
					<label for="font-color">Font Color:</label>
					<input type="color" id="font-color" data-cmd="font-color" data-cmd-type="change">
				</div>
				<div id="txt-style" class="txt-style">
					<div class="ln">
						<div style="margin-left: ${this._shapeData && !this._shapeData.t ? '67px' : '23px'}"></div>
						<svg data-cmd="txt-style" data-cmd-type="click" data-cmd-arg="bold" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 7.184 18.029 C 7.823 18.304 8.428 18.443 8.997 18.443 C 12.241 18.443 13.863 16.998 13.863 14.108 C 13.863 13.124 13.685 12.347 13.333 11.778 C 13.099 11.398 12.834 11.078 12.537 10.82 C 12.238 10.561 11.947 10.362 11.663 10.218 C 11.379 10.076 11.03 9.968 10.621 9.893 C 10.211 9.821 9.849 9.776 9.533 9.758 C 9.217 9.739 8.811 9.731 8.311 9.731 C 7.68 9.731 7.246 9.773 7.003 9.859 C 7.003 10.317 7.025 11.003 7.068 11.918 C 7.111 12.833 7.133 13.513 7.133 13.963 C 7.133 14.033 7.129 14.324 7.121 14.836 C 7.113 15.35 7.133 15.766 7.187 16.084 C 7.238 16.403 7.258 16.764 7.246 17.167 C 7.233 17.568 7.285 17.853 7.401 18.027 L 7.184 18.027 L 7.184 18.029 Z M 7.003 8.374 C 7.366 8.435 7.836 8.464 8.413 8.464 C 9.121 8.464 9.737 8.408 10.263 8.297 C 10.789 8.184 11.265 7.993 11.688 7.721 C 12.11 7.449 12.433 7.064 12.653 6.562 C 12.873 6.063 12.983 5.448 12.983 4.723 C 12.983 4.12 12.858 3.591 12.608 3.138 C 12.357 2.685 12.016 2.333 11.586 2.078 C 11.155 1.823 10.688 1.635 10.188 1.513 C 9.688 1.393 9.153 1.333 8.582 1.333 C 8.152 1.333 7.59 1.388 6.898 1.5 C 6.898 1.93 6.915 2.583 6.949 3.454 C 6.984 4.326 7.001 4.98 7.001 5.422 C 7.001 5.654 7.023 5.999 7.066 6.456 C 7.108 6.913 7.132 7.253 7.132 7.478 C 7.132 7.876 7.135 8.173 7.144 8.372 L 7.003 8.372 L 7.003 8.374 Z M 0 19.88 L 0.027 18.664 C 0.155 18.629 0.523 18.559 1.127 18.458 C 1.73 18.354 2.187 18.238 2.498 18.108 C 2.559 18.005 2.612 17.888 2.658 17.76 C 2.706 17.632 2.743 17.486 2.769 17.327 C 2.796 17.168 2.818 17.028 2.841 16.908 C 2.863 16.787 2.875 16.625 2.878 16.422 C 2.883 16.219 2.905 16.073 2.944 15.981 L 2.944 15.134 C 2.944 6.66 2.848 2.238 2.658 1.867 C 2.624 1.798 2.53 1.736 2.373 1.679 C 2.218 1.624 2.027 1.575 1.798 1.537 C 1.569 1.498 1.355 1.468 1.158 1.447 C 0.959 1.424 0.749 1.406 0.528 1.388 C 0.31 1.368 0.18 1.355 0.137 1.347 L 0.086 0.273 C 0.93 0.255 2.398 0.204 4.485 0.123 C 6.573 0.041 8.182 0 9.313 0 C 9.511 0 9.806 0.023 10.198 0.066 C 10.59 0.108 10.882 0.13 11.072 0.13 C 11.676 0.13 12.265 0.186 12.838 0.298 C 13.412 0.41 13.967 0.592 14.502 0.841 C 15.036 1.092 15.503 1.398 15.898 1.759 C 16.298 2.123 16.616 2.573 16.856 3.112 C 17.098 3.653 17.221 4.246 17.221 4.893 C 17.221 5.342 17.149 5.754 17.007 6.129 C 16.864 6.505 16.697 6.815 16.503 7.063 C 16.309 7.309 16.03 7.556 15.668 7.807 C 15.305 8.058 14.991 8.252 14.724 8.388 C 14.457 8.528 14.093 8.698 13.637 8.907 C 14.965 9.208 16.073 9.786 16.956 10.641 C 17.84 11.496 18.283 12.565 18.283 13.85 C 18.283 14.713 18.132 15.487 17.829 16.174 C 17.528 16.863 17.123 17.423 16.619 17.864 C 16.115 18.304 15.519 18.673 14.834 18.97 C 14.148 19.268 13.442 19.476 12.718 19.598 C 11.994 19.719 11.234 19.78 10.441 19.78 C 10.062 19.78 9.493 19.768 8.733 19.741 C 7.974 19.714 7.405 19.703 7.025 19.703 C 6.111 19.703 4.787 19.749 3.053 19.845 C 1.318 19.942 0.323 19.993 0.063 20 L 0 19.88 Z" fill="rgb(52,71,103)"/></svg>
						<svg data-cmd="txt-style" data-cmd-type="click" data-cmd-arg="italic" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 6.217 0 L 18.035 0 L 17.643 1.258 L 17.059 1.258 C 15.113 1.258 13.894 2.055 13.398 3.647 L 9.451 16.353 C 8.831 18.031 9.558 18.828 11.627 18.743 L 12.21 18.743 L 11.82 20 L 0 20 L 0.392 18.743 L 0.828 18.743 C 2.773 18.743 3.931 17.988 4.304 16.48 L 8.292 3.649 C 8.908 1.973 8.233 1.176 6.263 1.259 L 5.827 1.259 L 6.217 0 Z" fill="rgb(52,71,103)"/></svg>
						<svg data-cmd="txt-style" data-cmd-type="click" data-cmd-arg="underline" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 0.624 1.237 C 0.304 1.218 0.108 1.202 0.039 1.183 L 0 0.039 C 0.113 0.031 0.286 0.027 0.52 0.027 C 1.041 0.027 1.526 0.045 1.979 0.08 C 3.124 0.141 3.844 0.172 4.14 0.172 C 4.887 0.172 5.615 0.159 6.328 0.133 C 7.333 0.098 7.968 0.076 8.229 0.068 C 8.714 0.068 9.088 0.059 9.349 0.041 L 9.337 0.223 L 9.363 1.055 L 9.363 1.171 C 8.843 1.248 8.304 1.288 7.749 1.288 C 7.229 1.288 6.887 1.396 6.721 1.614 C 6.609 1.737 6.552 2.308 6.552 3.332 C 6.552 3.444 6.554 3.585 6.558 3.754 C 6.562 3.923 6.564 4.034 6.564 4.087 L 6.576 7.068 L 6.758 10.713 C 6.811 11.788 7.031 12.665 7.421 13.343 C 7.725 13.854 8.141 14.254 8.67 14.54 C 9.433 14.948 10.202 15.152 10.973 15.152 C 11.875 15.152 12.706 15.03 13.461 14.787 C 13.946 14.63 14.377 14.409 14.75 14.123 C 15.167 13.812 15.448 13.534 15.597 13.291 C 15.909 12.806 16.139 12.31 16.287 11.808 C 16.468 11.175 16.56 10.179 16.56 8.827 C 16.56 8.141 16.546 7.586 16.515 7.16 C 16.484 6.733 16.438 6.203 16.373 5.564 C 16.307 4.926 16.248 4.234 16.197 3.487 L 16.143 2.72 C 16.101 2.138 15.997 1.757 15.832 1.575 C 15.536 1.271 15.203 1.124 14.83 1.133 L 13.528 1.159 L 13.347 1.12 L 13.373 0 L 14.467 0 L 17.135 0.131 C 17.794 0.158 18.645 0.113 19.688 0 L 19.923 0.027 C 19.976 0.357 20 0.578 20 0.69 C 20 0.751 19.982 0.886 19.947 1.093 C 19.558 1.198 19.192 1.255 18.853 1.263 C 18.221 1.359 17.876 1.433 17.825 1.483 C 17.694 1.614 17.629 1.792 17.629 2.018 C 17.629 2.079 17.635 2.196 17.649 2.369 C 17.662 2.543 17.67 2.677 17.67 2.773 C 17.739 2.938 17.835 4.656 17.956 7.929 C 18.008 9.621 17.943 10.941 17.76 11.888 C 17.629 12.547 17.452 13.077 17.225 13.475 C 16.894 14.038 16.409 14.573 15.766 15.077 C 15.115 15.57 14.326 15.958 13.398 16.236 C 12.451 16.521 11.345 16.666 10.078 16.666 C 8.629 16.666 7.397 16.466 6.38 16.068 C 5.348 15.66 4.571 15.132 4.05 14.481 C 3.522 13.822 3.161 12.975 2.969 11.943 C 2.83 11.248 2.761 10.22 2.761 8.858 L 2.761 4.518 C 2.761 2.885 2.688 1.961 2.54 1.744 C 2.322 1.433 1.683 1.263 0.624 1.237 Z M 19.996 19.58 L 19.996 18.748 C 19.996 18.625 19.958 18.527 19.88 18.448 C 19.802 18.37 19.703 18.331 19.58 18.331 L 0.416 18.331 C 0.294 18.331 0.196 18.37 0.117 18.448 C 0.039 18.525 0 18.625 0 18.748 L 0 19.58 C 0 19.703 0.039 19.8 0.117 19.88 C 0.194 19.958 0.294 19.996 0.416 19.996 L 19.58 19.996 C 19.703 19.996 19.8 19.958 19.88 19.88 C 19.958 19.8 19.996 19.7 19.996 19.58 Z" fill="rgb(52,71,103)"/></svg>
					</div>
				</div>
			</div>
			<div id="border" class="border" style="display: none;">
				<div class="form-div">
					<label for="border-width">Border Width:</label>
					<input type="number" id="border-width" data-cmd="border-width" data-cmd-type="change" min="0" max="50" step="0.5">
				</div>
				<div class="form-div">
					<label for="border-color">Border Color:</label>
					<input type="color" id="border-color" data-cmd="border-color" data-cmd-type="change">
				</div>
			</div>
			<div id="arrange" class="arrange" style="display: none;">
				<div class="ln">
					<div style="margin-left: ${!this._shapeData || this._shapeData.t || this._shapeData.pic ? '48px' : '90px'}"></div>
					<svg data-cmd="arrange" data-cmd-type="click" data-cmd-arg="bring-front" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 0 14.4 L 0 4.8 L 9.6 4.8 L 19.2 4.8 L 19.2 14.4 L 19.2 24 L 9.6 24 L 0 24 L 0 14.4 Z M 20.16 16.224 C 20.16 15.744 20.64 15.552 21.12 15.84 C 21.695 16.128 22.08 16.608 22.08 16.896 C 22.08 17.088 21.695 17.28 21.12 17.28 C 20.64 17.28 20.16 16.8 20.16 16.224 Z M 21.888 15.648 C 20.928 14.592 20.16 12.96 20.16 11.904 C 20.16 10.272 20.255 10.272 22.175 12.192 C 23.328 13.248 24 14.88 23.808 15.84 C 23.52 17.376 23.424 17.376 21.888 15.648 Z M 21.888 10.848 C 20.928 9.793 20.16 8.16 20.16 7.105 C 20.16 5.473 20.255 5.473 22.175 7.393 C 23.328 8.448 24 10.08 23.808 11.04 C 23.52 12.576 23.424 12.576 21.888 10.848 Z M 19.68 3.936 C 16.512 0.576 16.224 0 17.855 0 C 20.352 0 24.288 4.128 23.808 6.24 C 23.615 7.393 22.655 6.913 19.68 3.936 Z M 6.72 2.785 C 6.72 2.305 7.2 2.113 7.68 2.4 C 8.256 2.688 8.64 3.168 8.64 3.456 C 8.64 3.648 8.256 3.84 7.68 3.84 C 7.2 3.84 6.72 3.36 6.72 2.785 Z M 8.16 1.92 C 6.432 0.096 6.528 0 8.352 0 C 9.408 0 11.04 0.865 12 1.92 C 13.728 3.745 13.632 3.84 11.808 3.84 C 10.752 3.84 9.12 2.976 8.16 1.92 Z M 12.96 1.92 C 11.232 0.096 11.328 0 13.152 0 C 14.208 0 15.84 0.865 16.8 1.92 C 18.528 3.745 18.432 3.84 16.608 3.84 C 15.552 3.84 13.92 2.976 12.96 1.92 Z M 22.08 1.44 C 21.12 0.288 21.12 0 22.464 0 C 23.328 0 24 0.673 24 1.44 C 24 2.208 23.808 2.88 23.616 2.88 C 23.424 2.88 22.752 2.208 22.08 1.44 Z" fill="rgb(52,71,103)"/></svg>
					<svg data-cmd="arrange" data-cmd-type="click" data-cmd-arg="send-back" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 0 14.4 L 0 4.8 L 2.88 4.8 L 5.76 4.8 L 5.76 11.52 L 5.76 18.24 L 12.48 18.24 L 19.2 18.24 L 19.2 21.12 L 19.2 24 L 9.6 24 L 0 24 L 0 14.4 Z M 7.68 15.84 C 7.104 15.072 6.72 13.824 6.912 12.96 C 7.104 11.712 7.776 12 9.984 14.304 C 12.575 17.088 12.672 17.28 10.848 17.28 C 9.792 17.28 8.352 16.608 7.68 15.84 Z M 10.176 13.536 C 8.16 11.52 6.72 9.12 6.912 8.255 C 7.104 7.008 8.544 7.968 12.48 12 C 16.608 16.224 17.28 17.28 15.744 17.28 C 14.688 17.28 12.192 15.552 10.176 13.536 Z M 12.575 11.136 C 8.928 7.488 6.624 4.415 6.912 3.455 C 7.104 2.304 9.312 4.032 14.88 9.6 C 20.64 15.36 22.08 17.28 20.544 17.28 C 19.488 17.28 16.032 14.592 12.575 11.136 Z M 14.88 8.64 C 8.448 2.208 6.816 0 8.16 0 C 10.752 0 24.288 13.632 23.808 15.744 C 23.615 16.896 21.12 14.88 14.88 8.64 Z M 17.28 6.24 C 12.48 1.44 11.52 0 13.055 0 C 15.552 0 24.288 8.832 23.808 10.944 C 23.615 12.096 21.888 10.848 17.28 6.24 Z M 19.68 3.936 C 16.512 0.575 16.224 0 17.855 0 C 20.352 0 24.288 4.128 23.808 6.24 C 23.615 7.392 22.655 6.912 19.68 3.936 Z M 22.08 1.44 C 21.12 0.288 21.12 0 22.464 0 C 23.328 0 24 0.672 24 1.44 C 24 2.208 23.808 2.88 23.616 2.88 C 23.424 2.88 22.752 2.208 22.08 1.44 Z" fill="rgb(52,71,103)"/></svg>
				</div>
			</div>
			<div id="pictograms" class="pictograms" style="display: none;">
				<p class="title">Pictogram</p>
				<div class="pictograms-select form-div" id="pictograms-select">
					<label>Not Assigned</label>
					<div class="section">
						<div class="pictogram" id="default">
							<img src="${getPictogramUrl('default.svg')}" data-cmd="pictogram" data-cmd-arg="lavender" data-cmd-type="click">
						</div>
					</div>
					<label>SGA</label>
					<div class="section">
						<div class="pictogram" id="sga-acid">
							<img src="${getPictogramUrl('sga/acid.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-acid)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-aquatic-pollution">
							<img src="${getPictogramUrl('sga/aquatic-pollution.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-aquatic-pollution)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-bottle">
							<img src="${getPictogramUrl('sga/bottle.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-bottle)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-exclamation">
							<img src="${getPictogramUrl('sga/exclamation.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-exclamation)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-explosion">
							<img src="${getPictogramUrl('sga/explosion.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-explosion)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-flammable-gas">
							<img src="${getPictogramUrl('sga/flammable-gas.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-flammable-gas)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-round-flame">
							<img src="${getPictogramUrl('sga/round-flame.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-round-flame)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-silhouete">
							<img src="${getPictogramUrl('sga/silhouete.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-silhouete)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="sga-skull">
							<img src="${getPictogramUrl('sga/skull.svg')}" data-cmd="pictogram" data-cmd-arg="url(#sga-skull)" data-cmd-type="click">
						</div>
					</div>
					<label>United Nations</label>
					<div class="section">
						<div class="pictogram" id="un-acid8">
							<img src="${getPictogramUrl('united_nations/acid8.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-acid8)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-aquatic-pollution">
							<img src="${getPictogramUrl('united_nations/aquatic-pollution.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-aquatic-pollution)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-blue4">
							<img src="${getPictogramUrl('united_nations/blue4.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-blue4)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-explosives1">
							<img src="${getPictogramUrl('united_nations/explosives1.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-explosives1-1">
							<img src="${getPictogramUrl('united_nations/explosives1-1.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1-1)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-explosives1-2">
							<img src="${getPictogramUrl('united_nations/explosives1-2.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1-2)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-explosives1-3">
							<img src="${getPictogramUrl('united_nations/explosives1-3.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1-3)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-explosives1-4">
							<img src="${getPictogramUrl('united_nations/explosives1-4.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1-4)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-explosives1-5">
							<img src="${getPictogramUrl('united_nations/explosives1-5.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1-5)" data-cmd-type="click">
						</div>
					</div>
					<div class="section">
						<div class="pictogram" id="un-explosives1-6">
							<img src="${getPictogramUrl('united_nations/explosives1-6.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-explosives1-6)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-green2">
							<img src="${getPictogramUrl('united_nations/green2.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-green2)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-red2">
							<img src="${getPictogramUrl('united_nations/red2.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-red2)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-red3">
							<img src="${getPictogramUrl('united_nations/red3.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-red3)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-red-white4">
							<img src="${getPictogramUrl('united_nations/red-white4.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-red-white4)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-skull2">
							<img src="${getPictogramUrl('united_nations/skull2.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-skull2)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-skull6">
							<img src="${getPictogramUrl('united_nations/skull6.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-skull6)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-stripes4">
							<img src="${getPictogramUrl('united_nations/stripes4.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-stripes4)" data-cmd-type="click">
						</div>
						<div class="pictogram" id="un-yellow5-1">
							<img src="${getPictogramUrl('united_nations/yellow5-1.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-yellow5-1)" data-cmd-type="click">
						</div>
					</div>
					<div class="section">
						<div class="pictogram" id="un-yellow-red5-2">
							<img src="${getPictogramUrl('united_nations/yellow-red5-2.svg')}" data-cmd="pictogram" data-cmd-arg="url(#un-yellow-red5-2)" data-cmd-type="click">
						</div>
					</div>
				</div>
			</div>
			<div id="prop" style="display: none;"><slot id="slot"></slot></div>
		</div>
		<div class="ln">
			${!this._shapeData || (!this._shapeData.t && !this._shapeData.ipic) ?
				`<svg data-toggle="color" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M19.228 18.732l1.768-1.768 1.767 1.768a2.5 2.5 0 1 1-3.535 0zM8.878 1.08l11.314 11.313a1 1 0 0 1 0 1.415l-8.485 8.485a1 1 0 0 1-1.414 0l-8.485-8.485a1 1 0 0 1 0-1.415l7.778-7.778-2.122-2.121L8.88 1.08zM11 6.03L3.929 13.1 11 20.173l7.071-7.071L11 6.029z" fill="rgb(52,71,103)"/></svg>`
			: ''}
			<svg data-toggle="pictograms" ${this._shapeData && this._shapeData.ipic ? '' : 'style="display: none;"'} viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 12.906 0.375 C 12.407 -0.125 11.593 -0.125 11.094 0.375 L 0.375 11.094 C -0.125 11.593 -0.125 12.407 0.375 12.906 L 11.094 23.625 C 11.593 24.125 12.407 24.125 12.906 23.625 L 23.625 12.906 C 24.125 12.407 24.125 11.593 23.625 11.094 L 12.906 0.375 Z M 13.418 19.139 C 13.418 19.266 13.315 19.369 13.188 19.369 L 10.824 19.369 C 10.697 19.369 10.594 19.266 10.594 19.139 L 10.594 16.776 C 10.594 16.648 10.697 16.545 10.824 16.545 L 13.188 16.545 C 13.315 16.545 13.418 16.648 13.418 16.776 L 13.418 19.139 Z M 13.528 8.089 L 12.825 15.34 C 12.813 15.468 12.7 15.571 12.571 15.571 L 11.437 15.571 C 11.309 15.571 11.197 15.468 11.182 15.34 L 10.472 8.089 L 10.472 4.861 C 10.472 4.734 10.575 4.631 10.702 4.631 L 13.298 4.631 C 13.425 4.631 13.528 4.734 13.528 4.861 L 13.528 8.089 Z" fill="rgb(52,71,103)"/></svg>	
			<svg data-toggle="prop" ${this.getAttribute('edit-btn') == "true" ? '' : 'style="display: none;"'} viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M12.9 6.858l4.242 4.243L7.242 21H3v-4.243l9.9-9.9zm1.414-1.414l2.121-2.122a1 1 0 0 1 1.414 0l2.829 2.829a1 1 0 0 1 0 1.414l-2.122 2.121-4.242-4.242z" fill="rgb(52,71,103)"/></svg>
			<svg data-toggle="align" ${this.getAttribute('txt-btns') == "false" || this._shapeData.ta == false ? 'style="display: none;"' : ''} viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 3 4 L 21 4 L 21 6 L 3 6 L 3 4 Z M 2.996 18.957 L 21.004 18.915 L 21.004 20.915 L 3.039 20.829 L 2.996 18.957 Z M 3 14 L 21 14 L 21 16 L 3 16 L 3 14 Z M 2.996 8.872 L 20.961 8.786 L 21.003 10.829 L 2.996 10.915 L 2.996 8.872 Z" fill="rgb(52,71,103)"/></svg>
			<svg data-toggle="font" ${this.getAttribute('txt-btns') == "false" || this._shapeData.ta == false ? 'style="display: none;"' : ''} viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 13.066 17.744 L 11.483 17.744 Q 11.213 17.744 11.051 17.609 Q 10.888 17.474 10.798 17.272 L 9.54 13.723 L 3.453 13.723 L 2.207 17.261 Q 2.139 17.452 1.954 17.598 Q 1.769 17.744 1.51 17.744 L -0.073 17.744 L 5.463 2.987 L 7.541 2.987 Z M 3.97 12.264 L 9.024 12.264 L 6.935 6.323 Q 6.822 6.053 6.71 5.694 Q 6.598 5.334 6.497 4.919 Q 6.384 5.346 6.272 5.705 Q 6.16 6.064 6.059 6.334 Z M 21.857 17.744 Q 21.565 17.744 21.408 17.654 Q 21.251 17.564 21.195 17.284 L 20.948 16.262 Q 20.521 16.655 20.111 16.963 Q 19.701 17.272 19.252 17.486 Q 18.803 17.699 18.286 17.806 Q 17.769 17.912 17.152 17.912 Q 16.512 17.912 15.956 17.738 Q 15.4 17.564 14.979 17.199 Q 14.558 16.834 14.316 16.29 Q 14.075 15.745 14.075 15.004 Q 14.075 14.352 14.428 13.752 Q 14.782 13.151 15.58 12.679 Q 16.377 12.207 17.657 11.91 Q 18.937 11.612 20.802 11.567 L 20.802 10.725 Q 20.802 9.445 20.257 8.799 Q 19.712 8.153 18.668 8.153 Q 17.972 8.153 17.494 8.333 Q 17.017 8.513 16.669 8.726 Q 16.321 8.939 16.068 9.119 Q 15.815 9.299 15.557 9.299 Q 15.355 9.299 15.209 9.198 Q 15.063 9.097 14.973 8.939 L 14.614 8.31 Q 15.523 7.434 16.573 7.002 Q 17.623 6.57 18.904 6.57 Q 19.825 6.57 20.543 6.867 Q 21.262 7.165 21.745 7.715 Q 22.228 8.265 22.481 9.029 Q 22.733 9.793 22.733 10.725 L 22.733 17.744 Z M 17.747 16.531 Q 18.241 16.531 18.657 16.43 Q 19.072 16.329 19.443 16.144 Q 19.813 15.958 20.145 15.683 Q 20.476 15.408 20.802 15.071 L 20.802 12.803 Q 19.488 12.859 18.567 13.022 Q 17.646 13.184 17.068 13.454 Q 16.489 13.723 16.231 14.088 Q 15.973 14.453 15.973 14.903 Q 15.973 15.329 16.113 15.638 Q 16.253 15.947 16.489 16.144 Q 16.725 16.34 17.051 16.436 Q 17.376 16.531 17.747 16.531 Z" fill="rgb(52,71,103)"/></svg>
			<svg data-toggle="border" ${this.getAttribute('border-btns') == "false" || this._shapeData.t ? 'style="display: none;"' : ''} viewBox="0 0 24 24" width="24" height="24"><path fill="none" /><path d="M 0 0 L 0 24.037 L 24 24.037 L 24 0 L 0 0 Z M 20.016 20.035 L 3.913 20.035 L 3.913 4.033 L 20.016 4.033 L 20.016 20.035 Z" fill="rgb(52,71,103)"/></svg>			
			<svg data-toggle="arrange" ${this.getAttribute('arrange-btns') == "false" ? 'style="display: none;"' : ''} viewBox="0 0 24 24" width="24" height="24"><path d="M 19.555 14.224 L 19.555 3.556 L 17.777 3.556 L 17.777 14.224 L 13.332 14.224 L 18.666 19.558 L 24 14.224 L 19.555 14.224 Z M 7.112 1.778 L 7.112 7.112 L 1.778 7.112 L 1.778 1.778 L 7.112 1.778 Z M 8.89 0 L 0 0 L 0 8.89 L 8.89 8.89 L 8.89 0 Z M 0 12.446 L 2.667 12.446 L 2.667 14.224 L 0 14.224 L 0 12.446 Z M 3.556 12.446 L 6.223 12.446 L 6.223 14.224 L 3.556 14.224 L 3.556 12.446 Z M 7.112 12.446 L 8.89 12.446 L 8.89 15.113 L 7.112 15.113 L 7.112 12.446 Z M 0 18.669 L 1.778 18.669 L 1.778 21.336 L 0 21.336 L 0 18.669 Z M 2.667 19.558 L 5.334 19.558 L 5.334 21.336 L 2.667 21.336 L 2.667 19.558 Z M 6.223 19.558 L 8.89 19.558 L 8.89 21.336 L 6.223 21.336 L 6.223 19.558 Z M 0 15.113 L 1.778 15.113 L 1.778 17.78 L 0 17.78 L 0 15.113 Z M 7.112 16.002 L 8.89 16.002 L 8.89 18.669 L 7.112 18.669 L 7.112 16.002 Z" fill="rgb(52,71,103)"/></svg>			
			${copySvg}
			${delSvg}
		</div>`;

			
			// add the class to the alignEl and the element properties to the selects/inputs, so the right values are displayed when the settings menu is open
			const alignEl = shadow.getElementById('align');
			const txtStyleEl = shadow.getElementById('txt-style');
			const pictogramSelectEl = shadow.getElementById('pictograms-select');
			if(this._shapeData !== undefined) {
				if(this._shapeData.ta) {  // only setup them when the shape allows text
					classAdd(alignEl, `ta-${this._shapeData.a ? this._shapeData.a : 2}`);  // center is the value by default if no provided
					this._shapeData.ts.forEach(element => {
						classAdd (txtStyleEl, `ts-${element}`);
					});
					shadow.getElementById('font-size').value = this._shapeData.fs;				shadow.getElementById('font-family').value = this._shapeData.ff;
					shadow.getElementById('font-color').value = this._shapeData.fc;
				}
				shadow.getElementById('border-color').value = this._shapeData.bc;
				shadow.getElementById('border-width').value = this._shapeData.bw;
				shadow.getElementById('element-color').value = this._shapeData.sc;

				if(this._shapeData.ipic){  // only for pictograms
					classAdd(pictogramSelectEl.querySelector(`#${getPictogramIdFromFillValue(this._shapeData.pic)}`), 'selected');
				}
			}

			//
			// tabs
			{
				const pnl = shadow.getElementById('pnl');

				/** @param {1|-1} coef */
				function modalSetTop(coef) {
					modalChangeTop(window.scrollY + coef * pnl.getBoundingClientRect().height); // window.scrollY fix IPhone keyboard
				}

				/** @type {HTMLElement} */
				let currentTab;

				clickForAll(shadow, '[data-toggle]', evt => {
					if (currentTab) {
						modalSetTop(1);
						display(currentTab, false);
					}

					const tab = shadow.getElementById(evtTargetAttr(evt, 'data-toggle'));
					if (currentTab !== tab) {
						display(tab, true);
						modalSetTop(-1);
						currentTab = tab;
					} else {
						currentTab = null;
					}
				});
			}

			//
			// commands

			clickForAll(shadow, '[data-cmd-type="click"]', evt => {
				var dataCmd = evtTargetAttr(evt, 'data-cmd');
				var dataCmdArg = evtTargetAttr(evt, 'data-cmd-arg');
				this.dispatchEvent(new CustomEvent('cmd', {
					detail: {
						cmd: dataCmd,
						arg: dataCmdArg,
						extra: {
							alignEl: dataCmd == 'txt-align' ? alignEl : null,
							txtStyleEl: dataCmd == 'txt-style' ? txtStyleEl : null,
							pictogramSelectEl: dataCmd == 'pictogram' ? pictogramSelectEl : null,
						}
					}
				}));
			});

			changeForAll(shadow, '[data-cmd-type="change"]', evt => {
				var dataCmd = evtTargetAttr(evt, 'data-cmd');
				var dataCmdArg = shadow.getElementById(dataCmd).value;
				this.dispatchEvent(new CustomEvent('cmd', {
					detail: {
						cmd: dataCmd,
						arg: dataCmdArg,
						extra: {}
					}
				}));
			});
		}
	}
	customElements.define('ap-shape-edit', ShapeEdit);


	/** @param {ElementCSSInlineStyle} el, @param {boolean} isDisp */
	function display(el, isDisp) { el.style.display = isDisp ? 'unset' : 'none'; }

	/**
	 * provides:
	 *  - shape move
	 *
	 *  - text editor
	 *  - standard edit panel
	 *  - onTextChange callback
	 * @param {CanvasElement} canvas
	 * @param {string} shapeHtml must have '<text data-key="text">'
	 * @param {ShapeData & { title?: string}} shapeData
	 * @param {SettingsPnlCreateFn=} settingsPnlCreateFn
	 * @param {{(txtEl:SVGTextElement):void}} onTextChange
	 * @param {Object} resizes
	 */
	function shapeCreate(canvas, shapeData, shapeHtml, resizes, onTextChange, settingsPnlCreateFn) {
		/** @type {ShapeElement} */
		const el = svgEl('g', `${shapeHtml}
		${Object.entries(resizes)
		.map(rc => `<circle data-key="${rc[0]}" data-shape-resize="${rc[0]}" data-resize-dir="${rc[1].dir}" data-evt-index="2" r="7" cx="0" cy="0" style="transform: translate(${rc[1].position.x}px, ${rc[1].position.y}px);" />`)
		.join()}`);

		const textSettings = {
			/** @type {SVGTextElement} */
			el: child(el, 'text'),
			/** vericale middle, em */
			vMid: 0
		};

		if(shapeData.ta) {  // only create it when the shape allows text	
			svgTextDraw(textSettings.el, textSettings.vMid, shapeData.title);
		}

		const shapeProc = shapeEditEvtProc(canvas, el, shapeData, textSettings,
			settingsPnlCreateFn,
			// onTextChange
			() => onTextChange(textSettings.el));

		return {
			el,
			resizes,
			draw: shapeProc.draw
		};
	}

	/**
	 * provides:
	 *  - shape move
	 *  - copy fn
	 *
	 *  - text editor
	 *  - standard edit panel
	 *  - onTextChange callback
	 * @param {CanvasElement} canvas
	 * @param {ShapeElement} svgGrp
	 * @param {ShapeData & { title?: string}} shapeData
	 * @param { {el:SVGTextElement, vMid: number} } textSettings vMid in em
	 * @param {{():void}} onTextChange
	 * @param {SettingsPnlCreateFn} settingsPnlCreateFn
	 */
	function shapeEditEvtProc(canvas, svgGrp, shapeData, textSettings, settingsPnlCreateFn, onTextChange) {
		/** @type {{dispose():void, draw():void}} */
		let textEditor;

		/** @type { {position:(bottomX:number, bottomY:number)=>void, del:()=>void} } */
		let settingsPnl;

		function unSelect() {
			textEditor?.dispose(); textEditor = null;
			settingsPnl?.del(); settingsPnl = null;
		}

		/** @param {string} txt */
		function onTxtChange(txt) {
			shapeData.title = txt;
			onTextChange();
		}

		const settingPnlCreate = settingsPnlCreateFn ?? settingsPnlCreate;
		const shapeProc = shapeEvtProc(canvas, svgGrp, shapeData,
			// onEdit
			() => {
				if(shapeData.ta) {  // only create it when the shape allows text
					textEditor = textareaCreate(textSettings.el, textSettings.vMid, shapeData.title, onTxtChange, onTxtChange);
				}
				const position = svgGrp.getBoundingClientRect();
				settingsPnl = settingPnlCreate(canvas, svgGrp, position.left + 10, position.top + 10);
			
			},
			// onUnselect
			unSelect
		);

		svgGrp[ShapeSmbl].del = function() {
			shapeProc.del();
			svgGrp.remove();
		};

		return {
			draw: () => {
				shapeProc.drawPosition();

				if (settingsPnl) {
					const position = svgGrp.getBoundingClientRect();
					settingsPnl.position(position.left + 10, position.top + 10);
				}

				if (textEditor) { textEditor.draw(); }
			}
		};
	}

	/**
	 * provides:
	 *  - shape move
	 *  - copy fn
	 *  - onEdit, onEditStop callbacks
	 * @param {CanvasElement} canvas
	 * @param {ShapeElement} svgGrp
	 * @param {ShapeData} shapeData
	 * @param {{():void}} onEdit
	 * @param {{():void}} onUnselect
	 */
	function shapeEvtProc(canvas, svgGrp, shapeData, onEdit, onUnselect) {
		classAdd(svgGrp, 'hovertrack');

		function drawPosition() {
			svgGrp.style.transform = `translate(${shapeData.position.x}px, ${shapeData.position.y}px)`;
		}
		/**
		 * @type {0|1|2}
		 * 0 - init, 1 - select/edit
		*/
		let state = 0;

		/** @type {()=>void} */
		let listenCopyDispose;

		function unSelect() {
			onUnselect();

			state = 0;
			classDel(svgGrp, 'select');

			canvasSelectionClearSet(canvas, null);
			if (listenCopyDispose) { listenCopyDispose(); listenCopyDispose = null;	}
		}

		const moveProcReset = moveEvtProc(
			canvas.ownerSVGElement,
			svgGrp,
			canvas[CanvasSmbl].data,
			shapeData.position,
			// onMoveStart
			/** @param {PointerEvent & { target: Element} } evt */
			evt => {
				unSelect();
			},
			// onMove
			drawPosition,
			// onMoveEnd
			_ => {
				placeToCell(shapeData.position, canvas[CanvasSmbl].data.cell);
				drawPosition();
			},
			// onClick
			_ => {
				// in edit mode
				if (state === 1) { return; }

				// to select/edit mode
				state = 1;
				classAdd(svgGrp, 'select');  
				onEdit();
				canvasSelectionClearSet(canvas, unSelect);
				listenCopyDispose = listenCopy(() => [svgGrp]);
			},
			// onOutdown
			unSelect);

		svgGrp[ShapeSmbl] = {

			drawPosition,

			data: shapeData
		};

		return {
			drawPosition,
			del: () => {
				unSelect();
				moveProcReset();
			}
		};
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { {position:Point, scale:number, cell:number} } CanvasData */

	/** @typedef { 'left' | 'right' | 'top' | 'bottom' } PathDir */
	/** @typedef { {position: Point, dir: PathDir} } PathEnd */

	/** @typedef { {type: string, position: Point} } ShapeData */
	/**
	@typedef {{
		drawPosition: ()=>void
		data: ShapeData
		del?: ()=>void
		draw?: ()=>void
		calculateSizeForManualResize?: ()=>object
	}} Shape
	 */

	/** @typedef { {(canvas:CanvasElement, shapeElement:ShapeElement, bottomX:number, bottomY:number):{position(btmX:number, btmY:number):void, del():void} } } SettingsPnlCreateFn */

	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef {import('./shape-smbl').ShapeElement} ShapeElement */
	/** @typedef {import('./path').Path} Path */
	/** @typedef {import('./path-smbl').PathElement} PathElement */

	/**
	 * @param {CanvasElement} canvas
	 * @param {CircleData} circleData
	 */
	function circle(canvas, circleData) {
		circleData.a = circleData.a ?? 2;  // text align - center by default
		circleData.ff = circleData.ff ?? 'Arial';  // font family
		circleData.fs = circleData.fs ?? '16px';  // font size
		circleData.fc = circleData.fc ?? "#000000";  // font color - black by default
		circleData.bw = circleData.bw ?? 2;  // border width
		circleData.bc = circleData.bc ?? "#000000";  // border color - black by default
		circleData.ts = circleData.ts ?? [];  // text styles (italic, bold, underline)
		circleData.sc = circleData.sc ?? "#ff6600";  // shape color - safety orange by default
		circleData.ar = circleData.ar ?? true;  // specifies if the shape needs to be autoresized or not
		circleData.ta = true;  // specifies if the shape has text allowed or not

		const templ = `
		<circle data-key="outer" data-evt-no data-evt-index="2" r="72" fill="transparent" stroke-width="0" />
		<circle data-key="highlight" r="50" fill="transparent" stroke-width="${circleData.bw + 10}"/>
		<circle data-key="main" r="48" fill="${circleData.sc}" stroke="${circleData.bc}" stroke-width="${circleData.bw}" />
		<text data-key="text" x="${circleTxtXByAlign(circleData)}" y="0" text-anchor="middle" style="pointer-events: none; 
		font-family: ${circleData.ff}; font-size: ${circleData.fs}; fill: ${circleData.fc};">&nbsp;</text>`;

		const shape = shapeCreate(canvas, circleData, templ,
			{
				right: { dir: 1, position: { x: 48, y: 0 } },
				left: { dir: -1, position: { x: -48, y: 0 } },
				bottom: { dir: 1, position: { x: 0, y: 48 } },
				top: { dir: -1, position: { x: 0, y: -48 } }
			},
			// onTextChange
			txtEl => {
				if(circleData.ar){  // only do something if autoresize is required, if not nothing needs to change
					const newRadius = textElRadius(txtEl, 48, 30);
					if (newRadius !== circleData.r) {
						circleData.r = newRadius;
						resize();
					}
				}
			});

		const txtEl = child(shape.el, 'text');

		let currentTxtAlign = circleData.a;
		let currentR = circleData.r;
		/** @param {boolean?=} fixTxtAlign */
		function resize(fixTxtAlign) {
			shape.resizes.right.position.x = circleData.r;
			shape.resizes.left.position.x = -circleData.r;
			shape.resizes.bottom.position.y = circleData.r;
			shape.resizes.top.position.y = -circleData.r;
			for (const resizeCircle in shape.resizes) {
				positionSet(child(shape.el, resizeCircle), shape.resizes[resizeCircle].position);
			}

			radiusSet(shape.el, 'outer', circleData.r + 24);
			radiusSet(shape.el, 'highlight', circleData.r + 2);
			radiusSet(shape.el, 'main', circleData.r);

			// if text align or width changed
			if (fixTxtAlign || currentTxtAlign !== circleData.a || currentR !== circleData.r) {
				let txtX;
				let posXDelta;
				switch (circleData.a) {
					// text align left
					case 1:
						txtX = -circleData.r + 6;
						posXDelta = (circleData.r - currentR) / 2;
						break;
					case 2:
						txtX = 0;
						posXDelta = 0;
						break;
					// text align right
					case 3:
						txtX = circleData.r - 6;
						posXDelta = (circleData.r - currentR) / - 2;
						break;
				}

				txtEl.x.baseVal[0].value = txtX;
				txtEl.querySelectorAll('tspan').forEach(ss => { ss.x.baseVal[0].value = txtX; });

				circleData.position.x += posXDelta;

				classDel(shape.el, `ta-${currentTxtAlign}`);
				classAdd(shape.el, `ta-${circleData.a}`);

				currentTxtAlign = circleData.a;
				currentR = circleData.r;
			}
			shape.draw();
		}

		// apply initiial classes
		classAdd(shape.el, `ta-${circleData.a}`);
		circleData.ts.forEach(element => {
			classAdd (shape.el, `ts-${element}`);
		});

		if (!!circleData.r && circleData.r !== 48) { resize(true); } else { shape.draw(); }

		shape.el[ShapeSmbl].draw = resize;
		shape.el[ShapeSmbl]. calculateSizeForManualResize = calculateRadioFromPoints;

		return shape.el;
	}

	/** @param {Element} svgGrp, @param {string} key, @param {number} r */
	function radiusSet(svgGrp, key, r) { /** @type {SVGCircleElement} */(child(svgGrp, key)).r.baseVal.value = r; }

	/**
	 * calc radius that cover all <tspan> in SVGTextElement
	 * origin is in the center of the circle
	 * @param {SVGTextElement} textEl
	 * @param {*} minR
	 * @param {*} step
	 */
	function textElRadius(textEl, minR, step) {
		const farthestPoint = svgTxtFarthestPoint(textEl);  
		return ceil(minR, step, Math.sqrt(farthestPoint.x ** 2 + farthestPoint.y ** 2));
	}

	/** @param {CircleData} circleData */
	const circleTxtXByAlign = circleData => circleData.a === 1
		? -40 // text align left
		: circleData.a === 2
			? 0 // text align middle
			: 40; // text align right

	/** 
	 * @param {CircleData} circleData 
	 * @param {Point} mouseDownPoint 
	 * @param {Point} currentPoint
	 * @param {number} direction  
	*/
	function calculateRadioFromPoints(circleData, mouseDownPoint, currentPoint, direction){
		const minRadio = 30;  // min radio allowed to prevent the circle from disappearing 
		const dx = (currentPoint.x - mouseDownPoint.x) * direction;
		const dy = (currentPoint.y - mouseDownPoint.y) * direction;
		const newSize = {r: Math.max(Math.abs(circleData.r + dx + dy), minRadio)};
		return newSize;
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('./shape-evt-proc').CanvasData } CanvasData */
	/** 
	@typedef { 
		type: string, position: Point, title?: string, 
		r?: number, 
		a?: 1|2|3, 
		ff?: string, fs?: string, fc?: string, 
		bw?: float, bc?: string, 
		ts?: string[], 
		sc?: string,
		ta: boolean
	} CircleData */

	class PathSettings extends HTMLElement {
		/**
	 	 * @param {CanvasElement} canvas
		 * @param {PathElement} pathElement
		 */
		constructor(canvas, pathElement) {
			super();
			/** @private */
			this._pathElement = pathElement;

			/** @private */
			this._canvas = canvas;

			/** @private */
			this._pathData = this._pathElement[PathSmbl].data;
		}

		connectedCallback() {
			const pathStyles = this._pathData.styles;
			const actStyle = style => this._pathData.styles?.includes(style) ? 'class="actv"' : '';

			const shadow = this.attachShadow({ mode: 'closed' });
			shadow.innerHTML = `
		<style>
			.ln { display: flex; }
			.ln > * {
				height: 24px;
				padding: 10px;
				fill-opacity: 0.3;
				stroke-opacity: 0.3;
			}
			[data-cmd] { cursor: pointer; }
			.actv { 
				fill-opacity: 1;
				stroke-opacity: 1;
			}

			.form-div {
				padding: 10px;
			}

			.form-div > * {
				font-size: 12px;
			}

			label {
				display: inline-block;
				font-weight: bold;
				width: 25%;
			}

			input {
				width: 55%;
			}
		</style>
		<ap-shape-edit id="edit" edit-btn="true" txt-btns="false" border-btns="false">
			<div class="form-div">
				<label for="path-stroke-width">Width:</label>
				<input type="number" id="path-stroke-width" data-cmd="path-stroke-width" data-cmd-type="change" min="1" max="100" step="0.5">
			</div>
			<div class="ln">
				<div style="margin-left:24px;"></div>
				<svg data-cmd data-cmd-type="click" data-cmd-arg="arw-s" ${actStyle('arw-s')} viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M7.828 11H20v2H7.828l5.364 5.364-1.414 1.414L4 12l7.778-7.778 1.414 1.414z" fill="rgb(52,71,103)"/></svg>
				<svg data-cmd data-cmd-type="click" data-cmd-arg="arw-e" ${actStyle('arw-e')} viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M16.172 11l-5.364-5.364 1.414-1.414L20 12l-7.778 7.778-1.414-1.414L16.172 13H4v-2z" fill="rgb(52,71,103)"/></svg>
				<svg data-cmd data-cmd-type="click" data-cmd-arg="dash" ${actStyle('dash')} viewBox="0 0 24 24" width="24" height="24"><path d="M 2,11 L 20,11" stroke="rgb(52,71,103)" style="stroke-dasharray: 4,3; stroke-width: 3;"></path></svg>
			</div>
		</ap-shape-edit>`;

			// add the element properties to the selects/inputs, so the right values are displayed when the settings menu is open
			shadow.getElementById('path-stroke-width').value = this._pathData.sw;
			shadow.querySelector("ap-shape-edit").shadowRoot.getElementById("element-color").value = this._pathData.sc;

			// colors, del
			listen(shadow.getElementById('edit'), 'cmd', /** @param {CustomEvent<{cmd:string, arg:string}>} evt */ evt => {
				switch (evt.detail.cmd) {
					case 'element-color': applyElementColor(this._pathElement, this._pathElement[PathSmbl].data, evt.detail.arg, "path"); break;
					case 'del': this._pathElement[PathSmbl].del(); break;
					case 'copy': copyAndPast(this._canvas, [this._pathElement]); break;
					case 'path-stroke-width': applyPathStrokeWidth(this._pathElement, this._pathData, Number.parseFloat(evt.detail.arg)); break;
					case 'arrange': arrangeElement(this._pathElement, evt.detail.arg); break;
				}
			});

			// arrows, dotted
			clickForAll(shadow, '[data-cmd-type="click"]', evt => {
				const argStyle = evtTargetAttr(evt, 'data-cmd-arg');
				const currentArr = pathStyles.indexOf(argStyle);
				if (currentArr > -1) {
					classDel(this._pathElement, argStyle);
					pathStyles.splice(currentArr, 1);
					classDel(evt.currentTarget, 'actv');
				} else {
					classAdd(this._pathElement, argStyle);
					pathStyles.push(argStyle);
					classAdd(evt.currentTarget, 'actv');
				}
			});

			changeForAll(shadow, '[data-cmd-type="change"]', evt => {
				var dataCmd = evtTargetAttr(evt, 'data-cmd');
				var dataCmdArg = shadow.getElementById(dataCmd).value;
				shadow.getElementById('edit').dispatchEvent(new CustomEvent('cmd', {
					detail: {
						cmd: dataCmd,
						arg: dataCmdArg
					}
				}));
			});
		}
	}
	customElements.define('ap-path-settings', PathSettings);

	/** @typedef { import('./path-smbl').PathElement } PathElement */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */

	/**
	 * @param {CanvasElement} canvas
	 * @param {PathData} pathData
	 */
	function path(canvas, pathData) {
		pathData.styles = pathData.styles ?? [];  // styles for arrows and others
		pathData.sw = pathData.sw ?? 2;  // stroke width
		pathData.sc = pathData.sc ?? "#495057";  // shape color - gray by default

		/** @type {PathElement} */
		const svgGrp = svgEl('g', `
		<path data-key="outer" d="M0 0" stroke="transparent" fill="none" />
		<path data-key="path" class="path" d="M0 0" stroke="${pathData.sc}" fill="none" style="pointer-events: none;" />
		<path data-key="highlight" d="M0 0" stroke="transparent" fill="none" style="pointer-events: none;" />
		<g data-key="start">
			<path data-key="arrow-start" class="path" d="M 0 0 L 10 5 L 0 10 z" stroke="${pathData.sc}" fill="${pathData.sc}" style="transform: translate(0, -5px)"/>
			<circle data-evt-index="1" r="7" stroke-width="0" data-path-resize="start"/>
		</g>
		<g data-key="end">
			<path data-key="arrow-end" class="path" d="M 0 0 L 10 5 L 0 10 z" stroke="${pathData.sc}" fill="${pathData.sc}" style="transform: translate(0, -5px)"/>
			<circle data-evt-index="1" r="7" stroke-width="0" data-path-resize="end"/>
		</g>`);
		classAdd(svgGrp, 'shpath');

		pathData.s.el = child(svgGrp, 'start');
		pathData.e.el = child(svgGrp, 'end');

		const paths = childs(svgGrp, 'path', 'outer', 'highlight');

		function draw() {
			const endDir = dirByAngle(pathData.s.data.position, pathData.e.data.position);
			pathData.e.data.dir = endDir; 
			pathData.s.data.dir = dirReverse(endDir); 
			

			// path
			const dAttr = pathCalc(pathData);
			paths.forEach(pp => pp.setAttribute('d', dAttr));

			// ends
			endDraw(pathData.s);
			endDraw(pathData.e);
		}

		/** @type { {position:(bottomX:number, bottomY:number)=>void, del:()=>void} } */
		let settingsPnl;
		function del() {
			unSelect();
			reset();
			svgGrp.remove();
		}

		/**
		 * @type {0|1}
		 * 0 - init, 1 - selected
		*/
		let state = 0;

		/** @type {()=>void} */
		let listenCopyDispose;

		/** @param {PointerEvent} evt */
		function select(evt) {
			// in edit mode
			
			if (state === 1) { return; }

			// to select/edit mode
			state = 1;
			const position = svgGrp.getBBox();
			settingsPnl = modalCreate(position.x - 10, position.y - 10, new PathSettings(canvas, svgGrp));
			classAdd(svgGrp, 'select');
			endSetEvtIndex(pathData.s, 2);
			endSetEvtIndex(pathData.e, 2);

			canvasSelectionClearSet(canvas, unSelect);
			listenCopyDispose = listenCopy(() => [svgGrp]);
		}
		/** @type { {():void} } */
		function unSelect() {
			state = 0;
			classDel(svgGrp, 'select');
			endSetEvtIndex(pathData.s, 1);
			endSetEvtIndex(pathData.e, 1);

			settingsPnl?.del();	settingsPnl = null;

			canvasSelectionClearSet(canvas, null);
			if (listenCopyDispose) { listenCopyDispose(); listenCopyDispose = null;	}
		}
		/** @type {'s'|'e'} */
		let movedEnd;

		const reset = moveEvtProc(
			canvas.ownerSVGElement,
			svgGrp,
			canvas[CanvasSmbl].data,
			// data.end.position,
			{
				get x() { return pathData[movedEnd]?.data.position.x; },
				set x(val) { if (movedEnd) { pathData[movedEnd].data.position.x = val; } },

				get y() { return pathData[movedEnd]?.data.position.y; },
				set y(val) { if (movedEnd) { pathData[movedEnd].data.position.y = val; } }
			},
			// onMoveStart
			/** @param {PointerEvent & { target: Element} } evt */ evt => {
				unSelect();

				movedEnd = pathData.e.el.contains(evt.target) ? 'e' : pathData.s.el.contains(evt.target) ? 's' : null;

				//
				// move whole path
				if (!movedEnd) {
					return;
				}
			},
			// onMove
			/** @param {PointerEventFixMovement} evt */
			evt => {
				if (!movedEnd) {
					moveWholePath(canvas[CanvasSmbl].data, pathData, draw, evt);
				} else {
					draw();
				}
			},
			// onMoveEnd
			evt => {
				if (!movedEnd) {
					moveWholePathFinish(canvas[CanvasSmbl].data, pathData, draw);
				} else {
					draw();
				}

				// hover emulation - end
				unSelect();
			},
			// onClick
			select,
			// onOutdown
			unSelect
		);

		svgGrp[PathSmbl] = {
			draw,
			/** @param {PointerEventInit} evt */
			pointerCapture: evt => pathData.e.el.dispatchEvent(new PointerEvent('pointerdown', evt)),
			del,
			data: pathData
		};

		if (pathData.styles) { classAdd(svgGrp, ...pathData.styles); }

		// apply initial stroke width
		applyPathStrokeWidth(svgGrp, pathData, pathData.sw);
		
		draw();

		return svgGrp;
	}

	/**
	 * @param {{scale:number}} canvasData
	 * @param {PathData} pathData
	 * @param {{():void}} draw
	 * @param {PointerEventFixMovement} evt
	 */
	function moveWholePath(canvasData, pathData, draw, evt) {
		/** @param {Point} point */
		const move = point => movementApplay(point, canvasData.scale, evt);
		moveEnd(pathData.s, move);
		moveEnd(pathData.e, move);

		draw();
	}

	/**
	 * @param {{cell:number}} canvasData
	 * @param {PathData} pathData
	 * @param {{():void}} draw
	 */
	function moveWholePathFinish(canvasData, pathData, draw) {
		/** @param {Point} point */
		const toCell = point => placeToCell(point, canvasData.cell);
		moveEnd(pathData.s, toCell);
		moveEnd(pathData.e, toCell);

		draw();
	}

	/**
	 * applay moveFn to path end point
	 * @param {PathEnd} pathEnd, @param {{(point:Point):void}} moveFn */
	function moveEnd(pathEnd, moveFn) {
			moveFn(pathEnd.data.position);
	}

	/** @param {PathEnd} pathEnd */
	function endDraw(pathEnd) {
		pathEnd.el.style.transform = `translate(${pathEnd.data.position.x}px, ${pathEnd.data.position.y}px) rotate(${arrowAngle(pathEnd.data.dir)}deg)`;
	}

	/** @param {PathEnd} pathEnd, @param {number} index */
	function endSetEvtIndex(pathEnd, index) { pathEnd.el.firstElementChild.setAttribute('data-evt-index', index.toString()); }

	/** @param {Dir} dir */
	const arrowAngle = dir => dir === 'right'
		? 180
		: dir === 'left'
			? 0
			: dir === 'bottom'
				? 270
				: 90;

	/** @param {Dir} dir, @return {Dir} */
	const dirReverse = dir =>	dir === 'left'
		? 'right'
		: dir === 'right'
			? 'left'
			: dir === 'top' ? 'bottom' : 'top';

	/** @param {Point} s, @param {Point} e, @return {Dir} */
	function dirByAngle(s, e) {
		const rad = Math.atan2(e.y - s.y, e.x - s.x);
		return numInRangeIncludeEnds(rad, -0.8, 0.8)
			? 'left'
			: numInRangeIncludeEnds(rad, 0.8, 2.4)
				? 'top'
				: numInRangeIncludeEnds(rad, 2.4, 3.2) || numInRangeIncludeEnds(rad, -3.2, -2.4) ? 'right' : 'bottom';
	}

	/** @param {PathData} data */
	function pathCalc(data) {
		let coef = Math.hypot(
			data.s.data.position.x - data.e.data.position.x,
			data.s.data.position.y - data.e.data.position.y) * 0.5;
		coef = coef > 70
			? 70
			: coef < 15 ? 15 : coef;

		/** @param {PathEndData} pathEnd */
		function cx(pathEnd) {
			return (pathEnd.dir === 'right' || pathEnd.dir === 'left')
				? pathEnd.dir === 'right' ? pathEnd.position.x + coef : pathEnd.position.x - coef
				: pathEnd.position.x;
		}

		/** @param {PathEndData} pathEnd */
		function cy(pathEnd) {
			return (pathEnd.dir === 'right' || pathEnd.dir === 'left')
				? pathEnd.position.y
				: pathEnd.dir === 'bottom' ? pathEnd.position.y + coef : pathEnd.position.y - coef;
		}

		return `M ${data.s.data.position.x} ${data.s.data.position.y} C ${cx(data.s.data)} ${cy(data.s.data)}, ` +
			`${cx(data.e.data)} ${cy(data.e.data)}, ${data.e.data.position.x} ${data.e.data.position.y}`;
	}

	/** @param {Element} el, @param  {...string} keys */
	const childs = (el, ...keys) => keys.map(kk => child(el, kk));

	/** @param {number} num, @param {number} a, @param {number} b */
	const numInRangeIncludeEnds = (num, a, b) => a <= num && num <= b;

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { 'left' | 'right' | 'top' | 'bottom' } Dir */
	/** @typedef { {position: Point, dir: Dir }} PathEndData */
	/**
	@typedef {{
		type: string,
		s: PathEnd,
		e: PathEnd,
		styles?: string[],
		sw?: float,
		sc?: string
	}} PathData
	*/

	/**
	@typedef {{
		draw(): void
		pointerCapture: (evt:PointerEventInit)=>void
		del(): void
		data: PathData
	}} Path
	*/

	/** @typedef { import('./path-smbl.js').PathElement } PathElement */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('../infrastructure/move-evt-mobile-fix.js').PointerEventFixMovement } PointerEventFixMovement */

	/**
	 * @param {CanvasElement} canvas
	 * @param {PictogramData} pictogramData
	 */
	function pictogram(canvas, pictogramData) {
		pictogramData.w = pictogramData.w ?? 96;  // width 
		pictogramData.bw = pictogramData.bw ?? 0;  // border width
		pictogramData.bc = pictogramData.bc ?? "#000000";  // border color - black by default
		pictogramData.ar = pictogramData.ar ?? true;  // specifies if the shape needs to be autoresized or not
		pictogramData.ta = false;  // specifies if the shape has text allowed or not
		pictogramData.ipic = true;  // specifices if the shape is a pictogram, so it has special attirbutes and menu options
		pictogramData.pic = pictogramData.pic ?? 'lavender';  // pictogram image url - use a simple color by default

		const templ = `
		<path data-key="outer" data-evt-no data-evt-index="2" d="M-72 0 L0 -72 L72 0 L0 72 Z" stroke-width="0" fill="transparent" />
		<path data-key="highlight" d="M-40 0 L0 -40 L40 0 L0 40 Z" fill="transparent" stroke-linejoin="round" stroke-width="${pictogramData.bw + 10}"/>
		<path data-key="main" d="M-39 0 L0 -39 L39 0 L0 39 Z" fill="${pictogramData.pic}" stroke="${pictogramData.bc}" stroke-width="${pictogramData.bw}"/>`;
		const shape = shapeCreate(canvas, pictogramData, templ,
			{
				right: { dir: 1, position: { x: 48, y: 0 } },
				left: { dir: -1, position: { x: -48, y: 0 } },
				bottom: { dir: 1, position: { x: 0, y: 48 } },
				top: { dir: -1, position: { x: 0, y: -48 } }
			},
			// onTextChange -- do nothing since no text allowed
			{}
		);

		classAdd(shape.el, 'shpictogram');

		function resize() {
			const connectors = pictogramCalc(pictogramData.w, 0);
			shape.resizes.right.position.x = connectors.r.x;
			shape.resizes.left.position.x = connectors.l.x;
			shape.resizes.bottom.position.y = connectors.b.y;
			shape.resizes.top.position.y = connectors.t.y;
			for (const resizeCircle in shape.resizes) {
				positionSet(child(shape.el, resizeCircle), shape.resizes[resizeCircle].position);
			}

			pictogramSet(shape.el, 'outer', pictogramCalc(pictogramData.w, -24));
			pictogramSet(shape.el, 'highlight', pictogramCalc(pictogramData.w, 8));
			pictogramSet(shape.el, 'main', pictogramCalc(pictogramData.w, 9));
			
			shape.draw();
		}

		if (!!pictogramData.w && pictogramData.w !== 96) { resize(); } else { shape.draw(); }

		shape.el[ShapeSmbl].draw = resize;
		shape.el[ShapeSmbl].calculateSizeForManualResize = calculateWidthFromPoints$1;

		return shape.el;
	}

	/**
	 * @param {Element} svgGrp, @param {string} key,
	 * @param {PictogramPoints} pictogram
	 */
	function pictogramSet(svgGrp, key, pictogram) {
		/** @type {SVGPathElement} */(child(svgGrp, key)).setAttribute('d', `M${pictogram.l.x} ${pictogram.l.y} L${pictogram.t.x} ${pictogram.t.y} L${pictogram.r.x} ${pictogram.r.y} L${pictogram.b.x} ${pictogram.b.y} Z`);
	}

	/**
	 * calc square pictogram points by width
	 * origin is in the center of the pictogram
	 * @param {number} width, @param {number} margin
	 * @returns {PictogramPoints}
	 */
	function pictogramCalc(width, margin) {
		const half = width / 2;
		const mrgnMinHalf = margin - half;
		const halfMinMrgn = half - margin;
		var a =  {
			l: { x: mrgnMinHalf, y: 0 },
			t: { x: 0, y: mrgnMinHalf },
			r: { x: halfMinMrgn, y: 0 },
			b: { x: 0, y: halfMinMrgn }
		};
		return a
	}

	/** 
	 * @param {PictogramData} pictogramData 
	 * @param {Point} mouseDownPoint 
	 * @param {Point} currentPoint
	 * @param {number} direction  
	*/
	function calculateWidthFromPoints$1(pictogramData, mouseDownPoint, currentPoint, direction){
		const minWidth = 70;  // min width allowed to prevent the pictogram from disappearing 
		const dx = (currentPoint.x - mouseDownPoint.x) * direction;
		const dy = (currentPoint.y - mouseDownPoint.y) * direction;
		const newSize = {w: Math.max(Math.abs(pictogramData.w + dx + dy), minWidth)};
		return newSize;
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('./shape-evt-proc').CanvasData } CanvasData */
	/**
	@typedef {
		type: string, position: Point, title?: string,
		w?:number,
		bw?: float, bc?: string, 
		sc?: string,
		ta: bolean,
		ipic: boolean
	} PictogramData
	*/
	/** @typedef { { l:Point, t:Point, r:Point, b:Point } } PictogramPoints */

	/**
	 * @param {CanvasElement} canvas
	 * @param {RectData} rectData
	 */
	function rect(canvas, rectData) {

		rectData.w = rectData.w ?? 96;  // width 
		rectData.h = rectData.h ?? 48;  // height
		rectData.a = rectData.a ?? (rectData.t ? 1 : 2);  // text align - center by default for shape and left for text
		rectData.ff = rectData.ff ?? 'Arial';  // font family
		rectData.fs = rectData.fs ?? '16px';  // font size
		rectData.fc = rectData.fc ?? "#000000";  // font color - black by default
		rectData.bw = rectData.bw ?? 2;  // border width
		rectData.bc = rectData.bc ?? "#000000";  // border color - black by default
		rectData.ts = rectData.ts ?? [];   // text styles (italic, bold, underline)
		rectData.sc = rectData.sc ?? "#009900";  // shape color - green by default
		rectData.ar = rectData.ar ?? true;  // specifies if the shape needs to be autoresized or not
		rectData.ta = true;  // specifies if the shape has text allowed or not

		const templ = `
		<rect data-key="outer" data-evt-no data-evt-index="2" width="144" height="96" x="-72" y="-48" fill="transparent" stroke="transparent" stroke-width="0" />
		<rect data-key="highlight" width="100" height="52" x="-50" y="-26" rx="1" ry="1" fill="transparent" stroke-width="${rectData.bw + 10}" />
		<rect data-key="main" width="96" height="48" x="-48" y="-24" rx="0" ry="0" fill="${rectData.sc}" ${rectData.t ? '' : `stroke="${rectData.bc}" stroke-width="${rectData.bw}"`}  />
		<text data-key="text" y="0" x="${rectTxtXByAlign(rectData)}" style="pointer-events: none;
		font-family: ${rectData.ff}; font-size: ${rectData.fs}; fill: ${rectData.fc}">&nbsp;</text>`;

		const shape = shapeCreate(canvas, rectData, templ,
			{
				right: { dir: 1, position: { x: 48, y: 0 } },
				left: { dir: -1, position: { x: -48, y: 0 } },
				bottom: { dir: 1, position: { x: 0, y: 24 } },
				top: { dir: -1, position: { x: 0, y: -24 } }
			},
			// onTextChange
			txtEl => {
				if(rectData.ar) {  // only do something if autoresize is required, if not nothing needs to change
					const textBox = txtEl.getBBox();
					const newWidth = ceil(96, 48, textBox.width + (rectData.t ? 6 : 0)); // 6px right padding for text shape
					const newHeight = ceil(48, 48, textBox.height);

					if (rectData.w !== newWidth || rectData.h !== newHeight) {
						rectData.w = newWidth;
						rectData.h = newHeight;
						resize();
					}
				}
			},

			// settingsPnlCreateFn
			settingsPnlCreate);

		classAdd(shape.el, rectData.t ? 'shtxt' : 'shrect');
		const txtEl = child(shape.el, 'text');

		let currentW = rectData.w;
		let currentTxtAlign = rectData.a;
		/** @param {boolean?=} fixTxtAlign */
		function resize(fixTxtAlign) {
			const mainX = rectData.w / -2;
			const mainY = rectData.h / -2;
			const middleX = 0;

			shape.resizes.right.position.x = -mainX;
			shape.resizes.left.position.x = mainX;
			shape.resizes.bottom.position.y = -mainY;
			shape.resizes.bottom.position.x = middleX;
			shape.resizes.top.position.y = mainY;
			shape.resizes.top.position.x = middleX;
			for (const resizeCircle in shape.resizes) {
				positionSet(child(shape.el, resizeCircle), shape.resizes[resizeCircle].position);
			}

			rectSet(shape.el, 'outer', rectData.w + 48, rectData.h + 48, mainX - 24, mainY - 24);
			rectSet(shape.el, 'highlight', rectData.w + 4, rectData.h + 4, mainX - 2, mainY - 2);
			rectSet(shape.el, 'main', rectData.w, rectData.h, mainX, mainY);


			// if text align or width changed
			if (fixTxtAlign || currentTxtAlign !== rectData.a || currentW !== rectData.w) {
				let txtX;
				let posXDelta;
				switch (rectData.a) {
					// text align left
					case 1:
						txtX = mainX + 8;
						posXDelta = (rectData.w - currentW) / 2;
						break;
					case 2:
						txtX = 0;
						posXDelta = 0;
						break;
					// text align right
					case 3:
						txtX = -mainX - 8;
						posXDelta = (rectData.w - currentW) / -2;
						break;
				}

				txtEl.x.baseVal[0].value = txtX;
				txtEl.querySelectorAll('tspan').forEach(ss => { ss.x.baseVal[0].value = txtX; });

				rectData.position.x += posXDelta;

				classDel(shape.el, `ta-${currentTxtAlign}`);
				classAdd(shape.el, `ta-${rectData.a}`);

				currentTxtAlign = rectData.a;
				currentW = rectData.w;
			}

			shape.draw();
		}

		// apply initial classes
		classAdd(shape.el, `ta-${rectData.a}`);
		rectData.ts.forEach(element => {
			classAdd (shape.el, `ts-${element}`);
		});

		if (rectData.w !== 96 || rectData.h !== 48) { resize(true); } else { shape.draw(); }

		shape.el[ShapeSmbl].draw = resize;
		shape.el[ShapeSmbl].calculateSizeForManualResize = calculateWidthHeightFromPoints;

		return shape.el;
	}

	/**
	 * @param {Element} svgGrp, @param {string} key,
	 * @param {number} w, @param {number} h
	 * @param {number} x, @param {number} y
	 */
	function rectSet(svgGrp, key, w, h, x, y) {
		/** @type {SVGRectElement} */ const rect = child(svgGrp, key);
		rect.width.baseVal.value = w;
		rect.height.baseVal.value = h;
		rect.x.baseVal.value = x;
		rect.y.baseVal.value = y;
	}

	/** @param {RectData} rectData */
	const rectTxtXByAlign = rectData => rectData.a === 1
		? -40 // text align left
		: rectData.a === 2
			? 0 // text align middle
			: 40; // text align right


	/** 
	 * @param {RectData} rectData 
	 * @param {Point} mouseDownPoint 
	 * @param {Point} currentPoint
	 * @param {number} direction  
	*/
	function calculateWidthHeightFromPoints(rectData, mouseDownPoint, currentPoint, direction){
		const minWidth = 60;  // min width allowed to prevent the rectangle from disappearing 
		const minHeight = 30;  // min height allowed to prevent the rectangle from disappearing 
		const dx = (currentPoint.x - mouseDownPoint.x) * direction;
		const dy = (currentPoint.y - mouseDownPoint.y) * direction;
		const newSize = {w: Math.max(Math.abs(rectData.w + dx), minWidth), 
						 h: Math.max(Math.abs(rectData.h + dy), minHeight)};
		return newSize;
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('./shape-evt-proc').CanvasData } CanvasData */
	/**
	@typedef {
		type: string, position: Point, title?: string,
		w?:number, h?:number
		t?:boolean,
		a?: 1|2|3,
		ff?: string, fs?: string, fc?: string,
		bw?: float, bc?: string,
		ts? string[],
		sc?: string,
		ta: boolean
	} RectData */

	/**
	 * @param {CanvasElement} canvas
	 * @param {RhombData} rhombData
	 */
	function rhomb(canvas, rhombData) {
		rhombData.a = rhombData.a ?? 2;  // text align - center by default
		rhombData.ff = rhombData.ff ?? 'Arial';  // font family
		rhombData.fs = rhombData.fs ?? '16px';  // font size
		rhombData.fc = rhombData.fc ?? "#000000";  // font color - black by default
		rhombData.bw = rhombData.bw ?? 2;  // border width
		rhombData.bc = rhombData.bc ?? "#000000";  // border color - black by default
		rhombData.ts = rhombData.ts ?? [];  // text styles (italic, bold, underline)
		rhombData.sc = rhombData.sc ?? "#ffff33";  // shape color - yellow taxi by default
		rhombData.ar = rhombData.ar ?? true;  // specifies if the shape needs to be autoresized or not
		rhombData.ta = true;  // specifies if the shape has text allowed or not

		const templ = `
		<path data-key="outer" data-evt-no data-evt-index="2" d="M-72 0 L0 -72 L72 0 L0 72 Z" stroke-width="0" fill="transparent" />
		<path data-key="highlight" d="M-40 0 L0 -40 L40 0 L0 40 Z" fill="transparent" stroke-linejoin="round" stroke-width="${rhombData.bw + 10}"/>
		<path data-key="main" d="M-39 0 L0 -39 L39 0 L0 39 Z" fill="${rhombData.sc}" stroke="${rhombData.bc}" stroke-width="${rhombData.bw}" />
		<text data-key="text" x="${rhombTxtXByAlign(rhombData)}" y="0" text-anchor="middle" style="pointer-events: none;
		font-family: ${rhombData.ff}; font-size: ${rhombData.fs}; fill: ${rhombData.fc};">&nbsp;</text>`;
		const shape = shapeCreate(canvas, rhombData, templ,
			{
				right: { dir: 1, position: { x: 48, y: 0 } },
				left: { dir: -1, position: { x: -48, y: 0 } },
				bottom: { dir: 1, position: { x: 0, y: 48 } },
				top: { dir: -1, position: { x: 0, y: -48 } }
			},
			// onTextChange
			txtEl => {
				if(rhombData.ar){  // only do something if autoresize is required, if not nothing needs to change
					const newWidth = ceil(96, 48, textElRhombWidth(txtEl) - 20); // -20 experimental val
					if (newWidth !== rhombData.w) {
						rhombData.w = newWidth;
						resize();
					}
				}
			}
		);

		classAdd(shape.el, 'shrhomb');
		const txtEl = child(shape.el, 'text');

		let currentW = rhombData.w;
		let currentTxtAlign = rhombData.a;
		/** @param {boolean?=} fixTxtAlign */
		function resize(fixTxtAlign) {
			const connectors = rhombCalc(rhombData.w, 0);
			shape.resizes.right.position.x = connectors.r.x;
			shape.resizes.left.position.x = connectors.l.x;
			shape.resizes.bottom.position.y = connectors.b.y;
			shape.resizes.top.position.y = connectors.t.y;
			for (const resizeCircle in shape.resizes) {
				positionSet(child(shape.el, resizeCircle), shape.resizes[resizeCircle].position);
			}

			const mainX = rhombData.w / -2;
			const mainRhomb = rhombCalc(rhombData.w, 9);
			rhombSet(shape.el, 'outer', rhombCalc(rhombData.w, -24));
			rhombSet(shape.el, 'highlight', rhombCalc(rhombData.w, 8));
			rhombSet(shape.el, 'main', mainRhomb);

			// if text align or width changed
			if (fixTxtAlign || currentTxtAlign !== rhombData.a || currentW !== rhombData.w) {
				let txtX;
				let posXDelta;
				switch (rhombData.a) {
					// text align left
					case 1:
						txtX = mainX + 18;
						posXDelta = (rhombData.w - currentW) / 2;
						break;
					case 2:
						txtX = 0;
						posXDelta = 0;
						break;
					// text align right
					case 3:
						txtX = -mainX - 18;
						posXDelta = (rhombData.w - currentW) / - 2;
						break;
				}

				txtEl.x.baseVal[0].value = txtX;
				txtEl.querySelectorAll('tspan').forEach(ss => { ss.x.baseVal[0].value = txtX; });

				rhombData.position.x += posXDelta;

				classDel(shape.el, `ta-${currentTxtAlign}`);
				classAdd(shape.el, `ta-${rhombData.a}`);

				currentTxtAlign = rhombData.a;
				currentW = rhombData.w;
			}

			shape.draw();
		}

		// apply initiial classes
		classAdd(shape.el, `ta-${rhombData.a}`);
		rhombData.ts.forEach(element => {
			classAdd (shape.el, `ts-${element}`);
		});

		if (!!rhombData.w && rhombData.w !== 96) { resize(true); } else { shape.draw(); }

		shape.el[ShapeSmbl].draw = resize;
		shape.el[ShapeSmbl].calculateSizeForManualResize = calculateWidthFromPoints;

		return shape.el;
	}

	/**
	 * @param {Element} svgGrp, @param {string} key,
	 * @param {RhombPoints} rhomb
	 */
	function rhombSet(svgGrp, key, rhomb) {
		/** @type {SVGPathElement} */(child(svgGrp, key)).setAttribute('d', `M${rhomb.l.x} ${rhomb.l.y} L${rhomb.t.x} ${rhomb.t.y} L${rhomb.r.x} ${rhomb.r.y} L${rhomb.b.x} ${rhomb.b.y} Z`);
	}

	/**
	 * calc square rhomb points by width
	 * origin is in the center of the rhomb
	 * @param {number} width, @param {number} margin
	 * @returns {RhombPoints}
	 */
	function rhombCalc(width, margin) {
		const half = width / 2;
		const mrgnMinHalf = margin - half;
		const halfMinMrgn = half - margin;
		return {
			l: { x: mrgnMinHalf, y: 0 },
			t: { x: 0, y: mrgnMinHalf },
			r: { x: halfMinMrgn, y: 0 },
			b: { x: 0, y: halfMinMrgn }
		};
	}

	/**
	 * calc width of the square rhomb that cover all tspan in {textEl}
	 * origin is in the center of the rhomb
	 * @param {SVGTextElement} textEl
	 */
	function textElRhombWidth(textEl) {
		const farthestPoint = svgTxtFarthestPoint(textEl);
		return 2 * (Math.abs(farthestPoint.x) + Math.abs(farthestPoint.y));
	}

	/** @param {RhombData} rhombData */
	const rhombTxtXByAlign = rhombData => rhombData.a === 1
		? -34 // text align left
		: rhombData.a === 2
			? 0 // text align middle
			: 34; // text align right


	/** 
	 * @param {RhombData} rhombData 
	 * @param {Point} mouseDownPoint 
	 * @param {Point} currentPoint
	 * @param {number} direction  
	*/
	function calculateWidthFromPoints(rhombData, mouseDownPoint, currentPoint, direction){
		const minWidth = 70;  // min width allowed to prevent the rhomb from disappearing 
		const dx = (currentPoint.x - mouseDownPoint.x) * direction;
		const dy = (currentPoint.y - mouseDownPoint.y) * direction;
		const newSize = {w: Math.max(Math.abs(rhombData.w + dx + dy), minWidth)};
		return newSize;
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/** @typedef { import('./shape-evt-proc').CanvasData } CanvasData */
	/**
	@typedef {
		type:number, position: Point, title?: string,
		w?:number,
		a?: 1|2|3,
		ff?: string, fs?: string, fc?: string,
		bw?: float, bc?: string, 
		ts?: string[], 
		sc?: string,
		ta: boolean
	} RhombData
	*/
	/** @typedef { { l:Point, t:Point, r:Point, b:Point } } RhombPoints */

	/**
	 * @param {CanvasElement} canvas
	 * @returns {Record<number, ShapeType>}
	 */
	function shapeTypeMap(canvas) {
		return {
			"line": { create: shapeData => path(canvas, shapeData) },
			"circle": { create: shapeData => circle(canvas, shapeData) },
			"rect": { create: shapeData => rect(canvas, shapeData) },
			"text": { create: shapeData => { /** @type {RectData} */(shapeData).t = true; return rect(canvas, shapeData); } },
			"rhomb": { create: shapeData => rhomb(canvas, shapeData) },
			"pictogram": { create: shapeData => pictogram(canvas, shapeData) }
		};
	}

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('./rect.js').RectData } RectData */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */
	/**
	@typedef {{
		create: (shapeData)=>SVGGraphicsElement
	}} ShapeType
	*/

	/**
	 * save file to user
	 * @param {Blob} blob
	 * @param {string} name
	 */
	function fileSave(blob, name) { ('showSaveFilePicker' in window) ? fileSaveAs(blob) : fileDownload(blob, name); }

	/**
	 * save file with "File save as" dialog
	 * @param {Blob} blob
	 */
	async function fileSaveAs(blob) {
		try {
			// @ts-ignore
			const writable = await (await window.showSaveFilePicker({
				types: [
					{
						description: 'PNG Image',
						accept: {
							'image/png': ['.png']
						}
					}
				]
			})).createWritable();
			await writable.write(blob);
			await writable.close();
		} catch {
			alert('File not saved');
		}
	}

	/**
	 * save file with default download process
	 * @param {Blob} blob
	 * @param {string} name
	 */
	function fileDownload(blob, name) {
		const link = document.createElement('a');
		link.download = name;
		link.href = URL.createObjectURL(blob);
		link.click();
		URL.revokeObjectURL(link.href);
		link.remove();
	}

	/**
	 * @param {string} accept
	 * @param {BlobCallback} callBack
	 */
	function fileOpen(accept, callBack) {
		const input = document.createElement('input');
		input.type = 'file';
		input.multiple = false;
		input.accept = accept;
		input.onchange = async function() {
			callBack((!input.files?.length) ? null : input.files[0]);
		};
		input.click();
		input.remove();
	}

	/** @type {HTMLDivElement} */ let overlay;
	/** @param {boolean} isDisable */
	function uiDisable(isDisable) {
		if (isDisable && !overlay) {
			overlay = document.createElement('div');
			overlay.style.cssText = 'z-index: 2; position: fixed; left: 0; top: 0; width:100%; height:100%; background: #fff; opacity: 0';
			overlay.innerHTML =
			`<style>
		@keyframes blnk {
			0% { opacity: 0; }
			50% { opacity: 0.7; }
			100% {opacity: 0;}
		}
		.blnk { animation: blnk 1.6s linear infinite; }
		</style>`;
			overlay.classList.add('blnk');
			document.body.append(overlay);
		} else if (!isDisable) {
			overlay.remove();
			overlay = null;
		}
	}

	class Menu extends HTMLElement {
		connectedCallback() {
			const shadow = this.attachShadow({ mode: 'closed' });
			shadow.innerHTML = `
			<style>
			.menu {
				position: fixed;
				top: 15px;
				left: 15px;
				cursor: pointer;
			}
			#options {
				position: fixed;
				padding: 15px;
				box-shadow: 0px 0px 58px 2px rgb(34 60 80 / 20%);
				border-radius: 16px;
				background-color: rgba(255,255,255, .9);

				top: 0px;
				left: 0px;

				z-index: 1;
			}

			#options div, #options a { 
				color: rgb(13, 110, 253); 
				cursor: pointer; margin: 10px 0;
				display: flex;
				align-items: center;
				line-height: 25px;
				text-decoration: none;
			}
			#options div svg, #options a svg { margin-right: 10px; }
			</style>
			<svg id="menu" class="menu" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 4h18v2H3V4zm0 7h18v2H3v-2zm0 7h18v2H3v-2z" fill="rgb(52,71,103)"/></svg>
			<div id="options" style="visibility: hidden;">
			 	<div id="menu2" style="margin: 0 0 15px;"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 4h18v2H3V4zm0 7h18v2H3v-2zm0 7h18v2H3v-2z" fill="rgb(52,71,103)"/></svg></div>
				<div id="new"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M9 2.003V2h10.998C20.55 2 21 2.455 21 2.992v18.016a.993.993 0 0 1-.993.992H3.993A1 1 0 0 1 3 20.993V8l6-5.997zM5.83 8H9V4.83L5.83 8zM11 4v5a1 1 0 0 1-1 1H5v10h14V4h-8z" fill="rgb(52,71,103)"/></svg>New diagram</div>
				<div id="open"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 21a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h7.414l2 2H20a1 1 0 0 1 1 1v3h-2V7h-7.414l-2-2H4v11.998L5.5 11h17l-2.31 9.243a1 1 0 0 1-.97.757H3zm16.938-8H7.062l-1.5 6h12.876l1.5-6z" fill="rgb(52,71,103)"/></svg>Open diagram image</div>
				<div id="save"><svg viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M3 19h18v2H3v-2zm10-5.828L19.071 7.1l1.414 1.414L12 17 3.515 8.515 4.929 7.1 11 13.17V2h2v11.172z" fill="rgb(52,71,103)"/></svg>Save diagram image</div>
		 	</div>`;

			const options = shadow.getElementById('options');
			function toggle() { options.style.visibility = options.style.visibility === 'visible' ? 'hidden' : 'visible'; }

			/** @param {string} id, @param {()=>void} handler */
			function click(id, handler) {
				shadow.getElementById(id).onclick = _ => {
					uiDisable(true);
					handler();
					toggle();
					uiDisable(false);
				};
			}

			shadow.getElementById('menu').onclick = toggle;
			shadow.getElementById('menu2').onclick = toggle;

			click('new', () => { canvasClear(this._canvas); });

			click('save', () => {
				const serialized = serialize(this._canvas);
				if (serialized.s.length === 0) { alertEmpty(); return; }

				// TODO - change the img width and height sent to be whatever needs to be based on what is required instead of it being hardcoded
				dgrmPngCreate(
					this._canvas,
					JSON.stringify(serialized),
					20, 25,  // img size (width, height) in centimeters
					png => fileSave(png, 'dgrm.png'));
			});

			click('open', () =>
				fileOpen('.png', async png => await loadData(this._canvas, png))
			);
		}

		/** @param {CanvasElement} canvas */
		init(canvas) {
			/** @private */ this._canvas = canvas;

			// file drag to window
			document.body.addEventListener('dragover', evt => { evt.preventDefault(); });
			document.body.addEventListener('drop', async evt => {
				evt.preventDefault();

				if (evt.dataTransfer?.items?.length !== 1 ||
					evt.dataTransfer.items[0].kind !== 'file' ||
					evt.dataTransfer.items[0].type !== 'image/png') {
					alertCantOpen(); return;
				}

				await loadData(this._canvas, evt.dataTransfer.items[0].getAsFile());
			});
		}
	}customElements.define('ap-menu', Menu);

	/** @param {CanvasElement} canvas,  @param {Blob} png  */
	async function loadData(canvas, png) {
		const dgrmChunk = await dgrmPngChunkGet(png);
		if (!dgrmChunk) { alertCantOpen(); return; }
		deserialize(canvas, JSON.parse(dgrmChunk));
	}

	const alertCantOpen = () => alert('File cannot be read. Use the exact image file you got from the application.');
	const alertEmpty = () => alert('Diagram is empty');

	/** @typedef { {x:number, y:number} } Point */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */

	class ShapeMenu extends HTMLElement {
		connectedCallback() {
			const shadow = this.attachShadow({ mode: 'closed' });
			shadow.innerHTML =
				`<style>
			.menu {
				overflow-x: auto;
				padding: 0;
				position: fixed;
				top: 50%;
				left: 5px;
				transform: translateY(-50%);
				box-shadow: 0px 0px 58px 2px rgba(34, 60, 80, 0.2);
				border-radius: 16px;
				background-color: rgba(255,255,255, .9);
			}

			.content {
				white-space: nowrap;
				display: flex;
				flex-direction: column;
			}
			
			[data-cmd] {
				cursor: pointer;
			}

			.menu svg { padding: 10px; }
			.stroke {
				stroke: #344767;
				stroke-width: 2px;
				fill: transparent;
			}
		
			.menu .big {
				width: 62px;
				min-width: 62px;
			}

			@media only screen and (max-width: 700px) {
				.menu {
					width: 100%;
					border-radius: 0;
					bottom: 0;
					display: flex;
  					flex-direction: column;
					top: unset;
					left: unset;
					transform: unset;
				}

				.content {
					align-self: center;
					flex-direction: row;
				}
			}
			</style>
			<div id="menu" class="menu" style="touch-action: none;">
				<div class="content">
					<svg class="stroke" data-cmd="shapeAdd" data-cmd-arg="circle" viewBox="0 0 24 24" width="24" height="24"><circle r="9" cx="12" cy="12"></circle></svg>
					<svg class="stroke" data-cmd="shapeAdd" data-cmd-arg="rhomb" viewBox="0 0 24 24" width="24" height="24"><path d="M2 12 L12 2 L22 12 L12 22 Z" stroke-linejoin="round"></path></svg>
					<svg class="stroke" data-cmd="shapeAdd" data-cmd-arg="rect" viewBox="0 0 24 24" width="24" height="24"><rect x="2" y="4" width="20" height="16" rx="3" ry="3"></rect></svg>
					<svg data-cmd="shapeAdd" data-cmd-arg="line" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M 22.072 3.343 L 3.009 22.41 L 1.859 20.927 L 20.837 1.973 L 22.072 3.343 Z" fill="rgba(52,71,103,1)"/></svg>
					<svg class="stroke" data-cmd="shapeAdd" data-cmd-arg="pictogram" viewBox="0 0 24 24" width="24" height="24"><path d="M 0.62 11.999 L 12.001 1.044 L 23.381 11.999 L 12.001 22.956 L 0.62 11.999 Z M 11.683 6.851 L 11.588 6.851 C 11.059 6.866 10.553 7.028 10.159 7.309 C 10.008 7.427 9.902 7.575 9.855 7.739 C 9.84 7.779 9.84 7.791 9.84 7.869 C 9.84 7.95 9.84 7.965 9.855 8.011 C 9.865 8.064 10.781 12.986 10.79 13.068 C 10.866 13.508 11.374 13.816 11.924 13.757 C 12.369 13.707 12.719 13.424 12.778 13.068 C 12.794 12.967 13.706 8.056 13.719 8.008 C 13.729 7.962 13.729 7.946 13.729 7.874 C 13.729 7.788 13.729 7.756 13.706 7.696 C 13.627 7.475 13.449 7.29 13.202 7.173 C 12.794 6.955 12.312 6.841 11.821 6.851 L 11.678 6.851 L 11.683 6.851 Z M 11.778 14.465 L 11.722 14.465 C 11.251 14.48 10.818 14.679 10.567 14.999 C 10.349 15.256 10.256 15.569 10.306 15.876 C 10.352 16.197 10.545 16.49 10.848 16.704 C 11.11 16.882 11.445 16.98 11.792 16.983 C 12.285 16.976 12.744 16.777 13.016 16.448 C 13.234 16.188 13.324 15.872 13.273 15.562 C 13.248 15.419 13.197 15.279 13.121 15.146 C 12.875 14.736 12.358 14.472 11.787 14.465" stroke-linejoin="round"></path></svg>					
					<svg data-cmd="shapeAdd" data-cmd-arg="text" viewBox="0 0 24 24" width="24" height="24"><path fill="none" d="M0 0h24v24H0z"/><path d="M13 6v15h-2V6H5V4h14v2z" fill="rgba(52,71,103,1)"/></svg>
				</div>
			</div>`;

			const menu = shadow.getElementById('menu');
			menu.querySelectorAll('[data-cmd="shapeAdd"]').forEach(el => listen(el, 'pointerdown', this));
			listen(menu, 'pointerleave', this);
			listen(menu, 'pointerup', this);
			listen(menu, 'pointermove', this);
		};

		/** @param {CanvasElement} canvas */
		init(canvas) {
			/** @private */ this._canvas = canvas;
		}

		/** @param {PointerEvent & { currentTarget: Element }} evt */
		handleEvent(evt) {
			switch (evt.type) {
				case 'pointermove':
					if (!this._isNativePointerleaveTriggered) {
						// emulate pointerleave for mobile

						const pointElem = document.elementFromPoint(evt.clientX, evt.clientY);
						if (pointElem === this._pointElem) {
							return;
						}

						// pointerleave
						if (this._parentElem === this._pointElem) {
							// TODO: check mobile
							this._canvas.ownerSVGElement.setPointerCapture(evt.pointerId);
						}

						/**
						 * @type {Element}
						 * @private
						 */
						this._pointElem = pointElem;
					}
					break;
				case 'pointerleave':
					this._isNativePointerleaveTriggered = true;
					if (this._pressedShapeTemplKey != null) {
						// when shape drag out from menu panel
						this._shapeCreate(evt);
					}
					this._clean();
					break;
				case 'pointerdown':
					this._pressedShapeTemplKey = evt.currentTarget.getAttribute('data-cmd-arg');

					// for emulate pointerleave
					this._parentElem = document.elementFromPoint(evt.clientX, evt.clientY);
					this._pointElem = this._parentElem;
					this._isNativePointerleaveTriggered = null;
					break;
				case 'pointerup':
					this._clean();
					break;
			}
		}

		/**
		 * @param {PointerEvent} evt
		 * @private
		 */
		_shapeCreate(evt) {

			const evtPoint = pointInCanvas(this._canvas[CanvasSmbl].data, evt.clientX, evt.clientY);

			const shapeData = this._pressedShapeTemplKey === "line"
				? /** @type {import('../shapes/path.js').PathData} */({
					s: { data: { dir: 'right', position: { x: evtPoint.x - 24, y: evtPoint.y } } },
					e: { data: { dir: 'right', position: { x: evtPoint.x + 24, y: evtPoint.y } } }
				})
				: {
					type: this._pressedShapeTemplKey,
					position: {
						x: evtPoint.x,
						y: evtPoint.y
					},
					title: 'Text...'
				};

			const shapeEl = this._canvas[CanvasSmbl].shapeMap[this._pressedShapeTemplKey].create(shapeData);
			this._canvas.append(shapeEl);
			shapeEl.dispatchEvent(new PointerEvent('pointerdown', evt));
		}

		/** @private */
		_clean() {
			this._pressedShapeTemplKey = null;
			this._parentElem = null;
			this._pointElem = null;
		}
	}
	customElements.define('ap-menu-shape', ShapeMenu);

	/** @typedef { import('../shapes/shape-type-map.js').ShapeType } ShapeType */
	/** @typedef { import('../infrastructure/canvas-smbl.js').CanvasElement } CanvasElement */

	// @ts-ignore
	/** @type {import('./infrastructure/canvas-smbl.js').CanvasElement} */ const canvas = document.getElementById('canvas');
	const pictogram_path = canvas.dataset.pictogrampath || "shapes/pictograms";
	canvas[CanvasSmbl] = {
		data: {
			position: { x: 0, y: 0 },
			scale: 1,
			cell: 24
		},
		shapeMap: shapeTypeMap(canvas)
	};

	addPictogramPatterns(canvas, pictogram_path);  // append the pictogram patterns to the canvas so they can be used on the shape

	moveEvtMobileFix(canvas.ownerSVGElement);
	evtRouteApplay(canvas.ownerSVGElement);
	copyPastApplay(canvas);
	groupSelectApplay(canvas); // groupSelectApplay must go before moveScaleApplay
	moveScaleApplay(canvas);
	registerExternalEvents(canvas);

	/** @type { import('./ui/menu').Menu } */(document.getElementById('menu')).init(canvas);
	/** @type { import('./ui/shape-menu').ShapeMenu } */(document.getElementById('menu-shape')).init(canvas);

})();
