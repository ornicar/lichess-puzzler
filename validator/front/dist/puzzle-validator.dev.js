var PuzzleValidator = (function () {
	'use strict';

	function getDefaultExportFromCjs (x) {
		return x && x.__esModule && Object.prototype.hasOwnProperty.call(x, 'default') ? x['default'] : x;
	}

	function createCommonjsModule(fn, basedir, module) {
		return module = {
			path: basedir,
			exports: {},
			require: function (path, base) {
				return commonjsRequire(path, (base === undefined || base === null) ? module.path : base);
			}
		}, fn(module, module.exports), module.exports;
	}

	function getAugmentedNamespace(n) {
		if (n.__esModule) return n;
		var a = Object.defineProperty({}, '__esModule', {value: true});
		Object.keys(n).forEach(function (k) {
			var d = Object.getOwnPropertyDescriptor(n, k);
			Object.defineProperty(a, k, d.get ? d : {
				enumerable: true,
				get: function () {
					return n[k];
				}
			});
		});
		return a;
	}

	function commonjsRequire () {
		throw new Error('Dynamic requires are not currently supported by @rollup/plugin-commonjs');
	}

	function vnode(sel, data, children, text, elm) {
	    var key = data === undefined ? undefined : data.key;
	    return { sel: sel, data: data, children: children, text: text, elm: elm, key: key };
	}

	var array = Array.isArray;
	function primitive(s) {
	    return typeof s === 'string' || typeof s === 'number';
	}

	function createElement(tagName) {
	    return document.createElement(tagName);
	}
	function createElementNS(namespaceURI, qualifiedName) {
	    return document.createElementNS(namespaceURI, qualifiedName);
	}
	function createTextNode(text) {
	    return document.createTextNode(text);
	}
	function createComment(text) {
	    return document.createComment(text);
	}
	function insertBefore(parentNode, newNode, referenceNode) {
	    parentNode.insertBefore(newNode, referenceNode);
	}
	function removeChild(node, child) {
	    node.removeChild(child);
	}
	function appendChild(node, child) {
	    node.appendChild(child);
	}
	function parentNode(node) {
	    return node.parentNode;
	}
	function nextSibling(node) {
	    return node.nextSibling;
	}
	function tagName(elm) {
	    return elm.tagName;
	}
	function setTextContent(node, text) {
	    node.textContent = text;
	}
	function getTextContent(node) {
	    return node.textContent;
	}
	function isElement(node) {
	    return node.nodeType === 1;
	}
	function isText(node) {
	    return node.nodeType === 3;
	}
	function isComment(node) {
	    return node.nodeType === 8;
	}
	var htmlDomApi = {
	    createElement: createElement,
	    createElementNS: createElementNS,
	    createTextNode: createTextNode,
	    createComment: createComment,
	    insertBefore: insertBefore,
	    removeChild: removeChild,
	    appendChild: appendChild,
	    parentNode: parentNode,
	    nextSibling: nextSibling,
	    tagName: tagName,
	    setTextContent: setTextContent,
	    getTextContent: getTextContent,
	    isElement: isElement,
	    isText: isText,
	    isComment: isComment,
	};

	function addNS(data, children, sel) {
	    data.ns = 'http://www.w3.org/2000/svg';
	    if (sel !== 'foreignObject' && children !== undefined) {
	        for (var i = 0; i < children.length; ++i) {
	            var childData = children[i].data;
	            if (childData !== undefined) {
	                addNS(childData, children[i].children, children[i].sel);
	            }
	        }
	    }
	}
	function h(sel, b, c) {
	    var data = {}, children, text, i;
	    if (c !== undefined) {
	        data = b;
	        if (array(c)) {
	            children = c;
	        }
	        else if (primitive(c)) {
	            text = c;
	        }
	        else if (c && c.sel) {
	            children = [c];
	        }
	    }
	    else if (b !== undefined) {
	        if (array(b)) {
	            children = b;
	        }
	        else if (primitive(b)) {
	            text = b;
	        }
	        else if (b && b.sel) {
	            children = [b];
	        }
	        else {
	            data = b;
	        }
	    }
	    if (children !== undefined) {
	        for (i = 0; i < children.length; ++i) {
	            if (primitive(children[i]))
	                children[i] = vnode(undefined, undefined, undefined, children[i], undefined);
	        }
	    }
	    if (sel[0] === 's' && sel[1] === 'v' && sel[2] === 'g' &&
	        (sel.length === 3 || sel[3] === '.' || sel[3] === '#')) {
	        addNS(data, children, sel);
	    }
	    return vnode(sel, data, children, text, undefined);
	}

	function copyToThunk(vnode, thunk) {
	    thunk.elm = vnode.elm;
	    vnode.data.fn = thunk.data.fn;
	    vnode.data.args = thunk.data.args;
	    thunk.data = vnode.data;
	    thunk.children = vnode.children;
	    thunk.text = vnode.text;
	    thunk.elm = vnode.elm;
	}
	function init(thunk) {
	    var cur = thunk.data;
	    var vnode = cur.fn.apply(undefined, cur.args);
	    copyToThunk(vnode, thunk);
	}
	function prepatch(oldVnode, thunk) {
	    var i, old = oldVnode.data, cur = thunk.data;
	    var oldArgs = old.args, args = cur.args;
	    if (old.fn !== cur.fn || oldArgs.length !== args.length) {
	        copyToThunk(cur.fn.apply(undefined, args), thunk);
	        return;
	    }
	    for (i = 0; i < args.length; ++i) {
	        if (oldArgs[i] !== args[i]) {
	            copyToThunk(cur.fn.apply(undefined, args), thunk);
	            return;
	        }
	    }
	    copyToThunk(oldVnode, thunk);
	}
	var thunk = function thunk(sel, key, fn, args) {
	    if (args === undefined) {
	        args = fn;
	        fn = key;
	        key = undefined;
	    }
	    return h(sel, {
	        key: key,
	        hook: { init: init, prepatch: prepatch },
	        fn: fn,
	        args: args
	    });
	};

	function isUndef(s) { return s === undefined; }
	function isDef(s) { return s !== undefined; }
	var emptyNode = vnode('', {}, [], undefined, undefined);
	function sameVnode(vnode1, vnode2) {
	    return vnode1.key === vnode2.key && vnode1.sel === vnode2.sel;
	}
	function isVnode(vnode) {
	    return vnode.sel !== undefined;
	}
	function createKeyToOldIdx(children, beginIdx, endIdx) {
	    var i, map = {}, key, ch;
	    for (i = beginIdx; i <= endIdx; ++i) {
	        ch = children[i];
	        if (ch != null) {
	            key = ch.key;
	            if (key !== undefined)
	                map[key] = i;
	        }
	    }
	    return map;
	}
	var hooks = ['create', 'update', 'remove', 'destroy', 'pre', 'post'];
	function init$1(modules, domApi) {
	    var i, j, cbs = {};
	    var api = domApi !== undefined ? domApi : htmlDomApi;
	    for (i = 0; i < hooks.length; ++i) {
	        cbs[hooks[i]] = [];
	        for (j = 0; j < modules.length; ++j) {
	            var hook = modules[j][hooks[i]];
	            if (hook !== undefined) {
	                cbs[hooks[i]].push(hook);
	            }
	        }
	    }
	    function emptyNodeAt(elm) {
	        var id = elm.id ? '#' + elm.id : '';
	        var c = elm.className ? '.' + elm.className.split(' ').join('.') : '';
	        return vnode(api.tagName(elm).toLowerCase() + id + c, {}, [], undefined, elm);
	    }
	    function createRmCb(childElm, listeners) {
	        return function rmCb() {
	            if (--listeners === 0) {
	                var parent_1 = api.parentNode(childElm);
	                api.removeChild(parent_1, childElm);
	            }
	        };
	    }
	    function createElm(vnode, insertedVnodeQueue) {
	        var i, data = vnode.data;
	        if (data !== undefined) {
	            if (isDef(i = data.hook) && isDef(i = i.init)) {
	                i(vnode);
	                data = vnode.data;
	            }
	        }
	        var children = vnode.children, sel = vnode.sel;
	        if (sel === '!') {
	            if (isUndef(vnode.text)) {
	                vnode.text = '';
	            }
	            vnode.elm = api.createComment(vnode.text);
	        }
	        else if (sel !== undefined) {
	            // Parse selector
	            var hashIdx = sel.indexOf('#');
	            var dotIdx = sel.indexOf('.', hashIdx);
	            var hash = hashIdx > 0 ? hashIdx : sel.length;
	            var dot = dotIdx > 0 ? dotIdx : sel.length;
	            var tag = hashIdx !== -1 || dotIdx !== -1 ? sel.slice(0, Math.min(hash, dot)) : sel;
	            var elm = vnode.elm = isDef(data) && isDef(i = data.ns) ? api.createElementNS(i, tag)
	                : api.createElement(tag);
	            if (hash < dot)
	                elm.setAttribute('id', sel.slice(hash + 1, dot));
	            if (dotIdx > 0)
	                elm.setAttribute('class', sel.slice(dot + 1).replace(/\./g, ' '));
	            for (i = 0; i < cbs.create.length; ++i)
	                cbs.create[i](emptyNode, vnode);
	            if (array(children)) {
	                for (i = 0; i < children.length; ++i) {
	                    var ch = children[i];
	                    if (ch != null) {
	                        api.appendChild(elm, createElm(ch, insertedVnodeQueue));
	                    }
	                }
	            }
	            else if (primitive(vnode.text)) {
	                api.appendChild(elm, api.createTextNode(vnode.text));
	            }
	            i = vnode.data.hook; // Reuse variable
	            if (isDef(i)) {
	                if (i.create)
	                    i.create(emptyNode, vnode);
	                if (i.insert)
	                    insertedVnodeQueue.push(vnode);
	            }
	        }
	        else {
	            vnode.elm = api.createTextNode(vnode.text);
	        }
	        return vnode.elm;
	    }
	    function addVnodes(parentElm, before, vnodes, startIdx, endIdx, insertedVnodeQueue) {
	        for (; startIdx <= endIdx; ++startIdx) {
	            var ch = vnodes[startIdx];
	            if (ch != null) {
	                api.insertBefore(parentElm, createElm(ch, insertedVnodeQueue), before);
	            }
	        }
	    }
	    function invokeDestroyHook(vnode) {
	        var i, j, data = vnode.data;
	        if (data !== undefined) {
	            if (isDef(i = data.hook) && isDef(i = i.destroy))
	                i(vnode);
	            for (i = 0; i < cbs.destroy.length; ++i)
	                cbs.destroy[i](vnode);
	            if (vnode.children !== undefined) {
	                for (j = 0; j < vnode.children.length; ++j) {
	                    i = vnode.children[j];
	                    if (i != null && typeof i !== "string") {
	                        invokeDestroyHook(i);
	                    }
	                }
	            }
	        }
	    }
	    function removeVnodes(parentElm, vnodes, startIdx, endIdx) {
	        for (; startIdx <= endIdx; ++startIdx) {
	            var i_1 = void 0, listeners = void 0, rm = void 0, ch = vnodes[startIdx];
	            if (ch != null) {
	                if (isDef(ch.sel)) {
	                    invokeDestroyHook(ch);
	                    listeners = cbs.remove.length + 1;
	                    rm = createRmCb(ch.elm, listeners);
	                    for (i_1 = 0; i_1 < cbs.remove.length; ++i_1)
	                        cbs.remove[i_1](ch, rm);
	                    if (isDef(i_1 = ch.data) && isDef(i_1 = i_1.hook) && isDef(i_1 = i_1.remove)) {
	                        i_1(ch, rm);
	                    }
	                    else {
	                        rm();
	                    }
	                }
	                else { // Text node
	                    api.removeChild(parentElm, ch.elm);
	                }
	            }
	        }
	    }
	    function updateChildren(parentElm, oldCh, newCh, insertedVnodeQueue) {
	        var oldStartIdx = 0, newStartIdx = 0;
	        var oldEndIdx = oldCh.length - 1;
	        var oldStartVnode = oldCh[0];
	        var oldEndVnode = oldCh[oldEndIdx];
	        var newEndIdx = newCh.length - 1;
	        var newStartVnode = newCh[0];
	        var newEndVnode = newCh[newEndIdx];
	        var oldKeyToIdx;
	        var idxInOld;
	        var elmToMove;
	        var before;
	        while (oldStartIdx <= oldEndIdx && newStartIdx <= newEndIdx) {
	            if (oldStartVnode == null) {
	                oldStartVnode = oldCh[++oldStartIdx]; // Vnode might have been moved left
	            }
	            else if (oldEndVnode == null) {
	                oldEndVnode = oldCh[--oldEndIdx];
	            }
	            else if (newStartVnode == null) {
	                newStartVnode = newCh[++newStartIdx];
	            }
	            else if (newEndVnode == null) {
	                newEndVnode = newCh[--newEndIdx];
	            }
	            else if (sameVnode(oldStartVnode, newStartVnode)) {
	                patchVnode(oldStartVnode, newStartVnode, insertedVnodeQueue);
	                oldStartVnode = oldCh[++oldStartIdx];
	                newStartVnode = newCh[++newStartIdx];
	            }
	            else if (sameVnode(oldEndVnode, newEndVnode)) {
	                patchVnode(oldEndVnode, newEndVnode, insertedVnodeQueue);
	                oldEndVnode = oldCh[--oldEndIdx];
	                newEndVnode = newCh[--newEndIdx];
	            }
	            else if (sameVnode(oldStartVnode, newEndVnode)) { // Vnode moved right
	                patchVnode(oldStartVnode, newEndVnode, insertedVnodeQueue);
	                api.insertBefore(parentElm, oldStartVnode.elm, api.nextSibling(oldEndVnode.elm));
	                oldStartVnode = oldCh[++oldStartIdx];
	                newEndVnode = newCh[--newEndIdx];
	            }
	            else if (sameVnode(oldEndVnode, newStartVnode)) { // Vnode moved left
	                patchVnode(oldEndVnode, newStartVnode, insertedVnodeQueue);
	                api.insertBefore(parentElm, oldEndVnode.elm, oldStartVnode.elm);
	                oldEndVnode = oldCh[--oldEndIdx];
	                newStartVnode = newCh[++newStartIdx];
	            }
	            else {
	                if (oldKeyToIdx === undefined) {
	                    oldKeyToIdx = createKeyToOldIdx(oldCh, oldStartIdx, oldEndIdx);
	                }
	                idxInOld = oldKeyToIdx[newStartVnode.key];
	                if (isUndef(idxInOld)) { // New element
	                    api.insertBefore(parentElm, createElm(newStartVnode, insertedVnodeQueue), oldStartVnode.elm);
	                    newStartVnode = newCh[++newStartIdx];
	                }
	                else {
	                    elmToMove = oldCh[idxInOld];
	                    if (elmToMove.sel !== newStartVnode.sel) {
	                        api.insertBefore(parentElm, createElm(newStartVnode, insertedVnodeQueue), oldStartVnode.elm);
	                    }
	                    else {
	                        patchVnode(elmToMove, newStartVnode, insertedVnodeQueue);
	                        oldCh[idxInOld] = undefined;
	                        api.insertBefore(parentElm, elmToMove.elm, oldStartVnode.elm);
	                    }
	                    newStartVnode = newCh[++newStartIdx];
	                }
	            }
	        }
	        if (oldStartIdx <= oldEndIdx || newStartIdx <= newEndIdx) {
	            if (oldStartIdx > oldEndIdx) {
	                before = newCh[newEndIdx + 1] == null ? null : newCh[newEndIdx + 1].elm;
	                addVnodes(parentElm, before, newCh, newStartIdx, newEndIdx, insertedVnodeQueue);
	            }
	            else {
	                removeVnodes(parentElm, oldCh, oldStartIdx, oldEndIdx);
	            }
	        }
	    }
	    function patchVnode(oldVnode, vnode, insertedVnodeQueue) {
	        var i, hook;
	        if (isDef(i = vnode.data) && isDef(hook = i.hook) && isDef(i = hook.prepatch)) {
	            i(oldVnode, vnode);
	        }
	        var elm = vnode.elm = oldVnode.elm;
	        var oldCh = oldVnode.children;
	        var ch = vnode.children;
	        if (oldVnode === vnode)
	            return;
	        if (vnode.data !== undefined) {
	            for (i = 0; i < cbs.update.length; ++i)
	                cbs.update[i](oldVnode, vnode);
	            i = vnode.data.hook;
	            if (isDef(i) && isDef(i = i.update))
	                i(oldVnode, vnode);
	        }
	        if (isUndef(vnode.text)) {
	            if (isDef(oldCh) && isDef(ch)) {
	                if (oldCh !== ch)
	                    updateChildren(elm, oldCh, ch, insertedVnodeQueue);
	            }
	            else if (isDef(ch)) {
	                if (isDef(oldVnode.text))
	                    api.setTextContent(elm, '');
	                addVnodes(elm, null, ch, 0, ch.length - 1, insertedVnodeQueue);
	            }
	            else if (isDef(oldCh)) {
	                removeVnodes(elm, oldCh, 0, oldCh.length - 1);
	            }
	            else if (isDef(oldVnode.text)) {
	                api.setTextContent(elm, '');
	            }
	        }
	        else if (oldVnode.text !== vnode.text) {
	            if (isDef(oldCh)) {
	                removeVnodes(elm, oldCh, 0, oldCh.length - 1);
	            }
	            api.setTextContent(elm, vnode.text);
	        }
	        if (isDef(hook) && isDef(i = hook.postpatch)) {
	            i(oldVnode, vnode);
	        }
	    }
	    return function patch(oldVnode, vnode) {
	        var i, elm, parent;
	        var insertedVnodeQueue = [];
	        for (i = 0; i < cbs.pre.length; ++i)
	            cbs.pre[i]();
	        if (!isVnode(oldVnode)) {
	            oldVnode = emptyNodeAt(oldVnode);
	        }
	        if (sameVnode(oldVnode, vnode)) {
	            patchVnode(oldVnode, vnode, insertedVnodeQueue);
	        }
	        else {
	            elm = oldVnode.elm;
	            parent = api.parentNode(elm);
	            createElm(vnode, insertedVnodeQueue);
	            if (parent !== null) {
	                api.insertBefore(parent, vnode.elm, api.nextSibling(elm));
	                removeVnodes(parent, [oldVnode], 0, 0);
	            }
	        }
	        for (i = 0; i < insertedVnodeQueue.length; ++i) {
	            insertedVnodeQueue[i].data.hook.insert(insertedVnodeQueue[i]);
	        }
	        for (i = 0; i < cbs.post.length; ++i)
	            cbs.post[i]();
	        return vnode;
	    };
	}

	var snabbdom = /*#__PURE__*/Object.freeze({
		__proto__: null,
		init: init$1,
		h: h,
		thunk: thunk
	});

	Object.defineProperty(exports, "__esModule", { value: true });
	function updateClass(oldVnode, vnode) {
	    var cur, name, elm = vnode.elm, oldClass = oldVnode.data.class, klass = vnode.data.class;
	    if (!oldClass && !klass)
	        return;
	    if (oldClass === klass)
	        return;
	    oldClass = oldClass || {};
	    klass = klass || {};
	    for (name in oldClass) {
	        if (!klass[name]) {
	            elm.classList.remove(name);
	        }
	    }
	    for (name in klass) {
	        cur = klass[name];
	        if (cur !== oldClass[name]) {
	            elm.classList[cur ? 'add' : 'remove'](name);
	        }
	    }
	}
	exports.classModule = { create: updateClass, update: updateClass };
	exports.default = exports.classModule;

	var _class = /*#__PURE__*/Object.freeze({
		__proto__: null
	});

	Object.defineProperty(exports, "__esModule", { value: true });
	var xlinkNS = 'http://www.w3.org/1999/xlink';
	var xmlNS = 'http://www.w3.org/XML/1998/namespace';
	var colonChar = 58;
	var xChar = 120;
	function updateAttrs(oldVnode, vnode) {
	    var key, elm = vnode.elm, oldAttrs = oldVnode.data.attrs, attrs = vnode.data.attrs;
	    if (!oldAttrs && !attrs)
	        return;
	    if (oldAttrs === attrs)
	        return;
	    oldAttrs = oldAttrs || {};
	    attrs = attrs || {};
	    // update modified attributes, add new attributes
	    for (key in attrs) {
	        var cur = attrs[key];
	        var old = oldAttrs[key];
	        if (old !== cur) {
	            if (cur === true) {
	                elm.setAttribute(key, "");
	            }
	            else if (cur === false) {
	                elm.removeAttribute(key);
	            }
	            else {
	                if (key.charCodeAt(0) !== xChar) {
	                    elm.setAttribute(key, cur);
	                }
	                else if (key.charCodeAt(3) === colonChar) {
	                    // Assume xml namespace
	                    elm.setAttributeNS(xmlNS, key, cur);
	                }
	                else if (key.charCodeAt(5) === colonChar) {
	                    // Assume xlink namespace
	                    elm.setAttributeNS(xlinkNS, key, cur);
	                }
	                else {
	                    elm.setAttribute(key, cur);
	                }
	            }
	        }
	    }
	    // remove removed attributes
	    // use `in` operator since the previous `for` iteration uses it (.i.e. add even attributes with undefined value)
	    // the other option is to remove all attributes with value == undefined
	    for (key in oldAttrs) {
	        if (!(key in attrs)) {
	            elm.removeAttribute(key);
	        }
	    }
	}
	exports.attributesModule = { create: updateAttrs, update: updateAttrs };
	exports.default = exports.attributesModule;

	var attributes = /*#__PURE__*/Object.freeze({
		__proto__: null
	});

	var ctrl = createCommonjsModule(function (module, exports) {
	Object.defineProperty(exports, "__esModule", { value: true });
	class Ctrl {
	    constructor(data, redraw) {
	        this.data = data;
	        this.redraw = redraw;
	    }
	}
	exports.default = Ctrl;

	});

	var snabbdom_1 = /*@__PURE__*/getAugmentedNamespace(snabbdom);

	var view = createCommonjsModule(function (module, exports) {
	Object.defineProperty(exports, "__esModule", { value: true });

	function default_1(ctrl) {
	    return snabbdom_1.h('main', [
	        'snabbdom view',
	        JSON.stringify(ctrl.data)
	    ]);
	}
	exports.default = default_1;

	});

	var class_1 = /*@__PURE__*/getAugmentedNamespace(_class);

	var attributes_1 = /*@__PURE__*/getAugmentedNamespace(attributes);

	var main = createCommonjsModule(function (module, exports) {
	Object.defineProperty(exports, "__esModule", { value: true });
	exports.start = void 0;



	/* import { Chessground } from 'chessground'; */

	const patch = snabbdom_1.init([class_1.default, attributes_1.default]);

	function start(data) {
	    const element = document.querySelector('main');
	    let vnode;
	    function redraw() {
	        vnode = patch(vnode, view.default(ctrl$1));
	    }
	    const ctrl$1 = new ctrl.default(data, redraw);
	    const blueprint = view.default(ctrl$1);
	    element.innerHTML = '';
	    vnode = patch(element, blueprint);
	    redraw();
	}
	exports.start = start;

	});

	var main$1 = /*@__PURE__*/getDefaultExportFromCjs(main);

	return main$1;

}());
