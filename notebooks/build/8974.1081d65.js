"use strict";(self.webpackChunk_JUPYTERLAB_CORE_OUTPUT=self.webpackChunk_JUPYTERLAB_CORE_OUTPUT||[]).push([[8974],{48974:(e,t,r)=>{r.r(t),r.d(t,{JupyterLiteServer:()=>i,Router:()=>a});var s=r(22236),n=r(71088),o=r(79334);class a{constructor(){this._routes=[]}get(e,t){this._add("GET",e,t)}put(e,t){this._add("PUT",e,t)}post(e,t){this._add("POST",e,t)}patch(e,t){this._add("PATCH",e,t)}delete(e,t){this._add("DELETE",e,t)}async route(e){const t=new URL(e.url),{method:r}=e,{pathname:s}=t;for(const n of this._routes){if(n.method!==r)continue;const o=s.match(n.pattern);if(!o)continue;const a=o.slice(1);let i;if("PATCH"===n.method||"PUT"===n.method||"POST"===n.method)try{i=JSON.parse(await e.text())}catch{i=void 0}return n.callback.call(null,{pathname:s,body:i,query:Object.fromEntries(t.searchParams)},...a)}throw new Error("Cannot route "+e.method+" "+e.url)}_add(e,t,r){"string"==typeof t&&(t=new RegExp(t)),this._routes.push({method:e,pattern:t,callback:r})}}class i extends n.Application{constructor(e){var t;super(e),this.name="JupyterLite Server",this.namespace=this.name,this.version="unknown",this._router=new a,this._serviceManager=new s.ServiceManager({standby:"never",serverSettings:{...s.ServerConnection.makeSettings(),WebSocket:o.WebSocket,fetch:null!==(t=this.fetch.bind(this))&&void 0!==t?t:void 0}})}get router(){return this._router}get serviceManager(){return this._serviceManager}async fetch(e,t){if(!(e instanceof Request))throw Error("Request info is not a Request");return this._router.route(e)}attachShell(e){}evtResize(e){}registerPluginModule(e){let t=e.default;Object.prototype.hasOwnProperty.call(e,"__esModule")||(t=e),Array.isArray(t)||(t=[t]),t.forEach((e=>{try{this.registerPlugin(e)}catch(e){console.error(e)}}))}registerPluginModules(e){e.forEach((e=>{this.registerPluginModule(e)}))}}}}]);
//# sourceMappingURL=8974.1081d65.js.map