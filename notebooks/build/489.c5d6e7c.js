"use strict";(self.webpackChunk_JUPYTERLAB_CORE_OUTPUT=self.webpackChunk_JUPYTERLAB_CORE_OUTPUT||[]).push([[489],{36130:(e,n,t)=>{t.d(n,{Z:()=>s});var a=t(20559),r=t.n(a),o=t(93476),c=t.n(o)()(r());c.push([e.id,".cm-s-elegant span.cm-number, .cm-s-elegant span.cm-string, .cm-s-elegant span.cm-atom { color: #762; }\n.cm-s-elegant span.cm-comment { color: #262; font-style: italic; line-height: 1em; }\n.cm-s-elegant span.cm-meta { color: #555; font-style: italic; line-height: 1em; }\n.cm-s-elegant span.cm-variable { color: black; }\n.cm-s-elegant span.cm-variable-2 { color: #b11; }\n.cm-s-elegant span.cm-qualifier { color: #555; }\n.cm-s-elegant span.cm-keyword { color: #730; }\n.cm-s-elegant span.cm-builtin { color: #30a; }\n.cm-s-elegant span.cm-link { color: #762; }\n.cm-s-elegant span.cm-error { background-color: #fdd; }\n\n.cm-s-elegant .CodeMirror-activeline-background { background: #e8f2ff; }\n.cm-s-elegant .CodeMirror-matchingbracket { outline:1px solid grey; color:black !important; }\n","",{version:3,sources:["webpack://./../node_modules/codemirror/theme/elegant.css"],names:[],mappings:"AAAA,yFAAyF,WAAW,EAAE;AACtG,gCAAgC,WAAW,EAAE,kBAAkB,EAAE,gBAAgB,EAAE;AACnF,6BAA6B,WAAW,EAAE,kBAAkB,EAAE,gBAAgB,EAAE;AAChF,iCAAiC,YAAY,EAAE;AAC/C,mCAAmC,WAAW,EAAE;AAChD,kCAAkC,WAAW,EAAE;AAC/C,gCAAgC,WAAW,EAAE;AAC7C,gCAAgC,WAAW,EAAE;AAC7C,6BAA6B,WAAW,EAAE;AAC1C,8BAA8B,sBAAsB,EAAE;;AAEtD,kDAAkD,mBAAmB,EAAE;AACvE,4CAA4C,sBAAsB,EAAE,sBAAsB,EAAE",sourcesContent:[".cm-s-elegant span.cm-number, .cm-s-elegant span.cm-string, .cm-s-elegant span.cm-atom { color: #762; }\n.cm-s-elegant span.cm-comment { color: #262; font-style: italic; line-height: 1em; }\n.cm-s-elegant span.cm-meta { color: #555; font-style: italic; line-height: 1em; }\n.cm-s-elegant span.cm-variable { color: black; }\n.cm-s-elegant span.cm-variable-2 { color: #b11; }\n.cm-s-elegant span.cm-qualifier { color: #555; }\n.cm-s-elegant span.cm-keyword { color: #730; }\n.cm-s-elegant span.cm-builtin { color: #30a; }\n.cm-s-elegant span.cm-link { color: #762; }\n.cm-s-elegant span.cm-error { background-color: #fdd; }\n\n.cm-s-elegant .CodeMirror-activeline-background { background: #e8f2ff; }\n.cm-s-elegant .CodeMirror-matchingbracket { outline:1px solid grey; color:black !important; }\n"],sourceRoot:""}]);const s=c},93476:e=>{e.exports=function(e){var n=[];return n.toString=function(){return this.map((function(n){var t="",a=void 0!==n[5];return n[4]&&(t+="@supports (".concat(n[4],") {")),n[2]&&(t+="@media ".concat(n[2]," {")),a&&(t+="@layer".concat(n[5].length>0?" ".concat(n[5]):""," {")),t+=e(n),a&&(t+="}"),n[2]&&(t+="}"),n[4]&&(t+="}"),t})).join("")},n.i=function(e,t,a,r,o){"string"==typeof e&&(e=[[null,e,void 0]]);var c={};if(a)for(var s=0;s<this.length;s++){var i=this[s][0];null!=i&&(c[i]=!0)}for(var l=0;l<e.length;l++){var A=[].concat(e[l]);a&&c[A[0]]||(void 0!==o&&(void 0===A[5]||(A[1]="@layer".concat(A[5].length>0?" ".concat(A[5]):""," {").concat(A[1],"}")),A[5]=o),t&&(A[2]?(A[1]="@media ".concat(A[2]," {").concat(A[1],"}"),A[2]=t):A[2]=t),r&&(A[4]?(A[1]="@supports (".concat(A[4],") {").concat(A[1],"}"),A[4]=r):A[4]="".concat(r)),n.push(A))}},n}},20559:e=>{e.exports=function(e){var n=e[1],t=e[3];if(!t)return n;if("function"==typeof btoa){var a=btoa(unescape(encodeURIComponent(JSON.stringify(t)))),r="sourceMappingURL=data:application/json;charset=utf-8;base64,".concat(a),o="/*# ".concat(r," */"),c=t.sources.map((function(e){return"/*# sourceURL=".concat(t.sourceRoot||"").concat(e," */")}));return[n].concat(c).concat([o]).join("\n")}return[n].join("\n")}},30489:(e,n,t)=>{t.r(n),t.d(n,{default:()=>v});var a=t(1892),r=t.n(a),o=t(95760),c=t.n(o),s=t(38311),i=t.n(s),l=t(58192),A=t.n(l),m=t(38060),u=t.n(m),p=t(54865),d=t.n(p),f=t(36130),g={};g.styleTagTransform=d(),g.setAttributes=A(),g.insert=i().bind(null,"head"),g.domAPI=c(),g.insertStyleElement=u(),r()(f.Z,g);const v=f.Z&&f.Z.locals?f.Z.locals:void 0},1892:e=>{var n=[];function t(e){for(var t=-1,a=0;a<n.length;a++)if(n[a].identifier===e){t=a;break}return t}function a(e,a){for(var o={},c=[],s=0;s<e.length;s++){var i=e[s],l=a.base?i[0]+a.base:i[0],A=o[l]||0,m="".concat(l," ").concat(A);o[l]=A+1;var u=t(m),p={css:i[1],media:i[2],sourceMap:i[3],supports:i[4],layer:i[5]};if(-1!==u)n[u].references++,n[u].updater(p);else{var d=r(p,a);a.byIndex=s,n.splice(s,0,{identifier:m,updater:d,references:1})}c.push(m)}return c}function r(e,n){var t=n.domAPI(n);return t.update(e),function(n){if(n){if(n.css===e.css&&n.media===e.media&&n.sourceMap===e.sourceMap&&n.supports===e.supports&&n.layer===e.layer)return;t.update(e=n)}else t.remove()}}e.exports=function(e,r){var o=a(e=e||[],r=r||{});return function(e){e=e||[];for(var c=0;c<o.length;c++){var s=t(o[c]);n[s].references--}for(var i=a(e,r),l=0;l<o.length;l++){var A=t(o[l]);0===n[A].references&&(n[A].updater(),n.splice(A,1))}o=i}}},38311:e=>{var n={};e.exports=function(e,t){var a=function(e){if(void 0===n[e]){var t=document.querySelector(e);if(window.HTMLIFrameElement&&t instanceof window.HTMLIFrameElement)try{t=t.contentDocument.head}catch(e){t=null}n[e]=t}return n[e]}(e);if(!a)throw new Error("Couldn't find a style target. This probably means that the value for the 'insert' parameter is invalid.");a.appendChild(t)}},38060:e=>{e.exports=function(e){var n=document.createElement("style");return e.setAttributes(n,e.attributes),e.insert(n,e.options),n}},58192:(e,n,t)=>{e.exports=function(e){var n=t.nc;n&&e.setAttribute("nonce",n)}},95760:e=>{e.exports=function(e){var n=e.insertStyleElement(e);return{update:function(t){!function(e,n,t){var a="";t.supports&&(a+="@supports (".concat(t.supports,") {")),t.media&&(a+="@media ".concat(t.media," {"));var r=void 0!==t.layer;r&&(a+="@layer".concat(t.layer.length>0?" ".concat(t.layer):""," {")),a+=t.css,r&&(a+="}"),t.media&&(a+="}"),t.supports&&(a+="}");var o=t.sourceMap;o&&"undefined"!=typeof btoa&&(a+="\n/*# sourceMappingURL=data:application/json;base64,".concat(btoa(unescape(encodeURIComponent(JSON.stringify(o))))," */")),n.styleTagTransform(a,e,n.options)}(n,e,t)},remove:function(){!function(e){if(null===e.parentNode)return!1;e.parentNode.removeChild(e)}(n)}}}},54865:e=>{e.exports=function(e,n){if(n.styleSheet)n.styleSheet.cssText=e;else{for(;n.firstChild;)n.removeChild(n.firstChild);n.appendChild(document.createTextNode(e))}}}}]);
//# sourceMappingURL=489.c5d6e7c.js.map