(self.webpackChunk_JUPYTERLAB_CORE_OUTPUT=self.webpackChunk_JUPYTERLAB_CORE_OUTPUT||[]).push([[49906,27061,30500,66558,3580,27254,30564,66700,3810,27295,30660,81279,84791,4484,38394,81152,84841,4638,37541,80333],{49906:(t,e,s)=>{"use strict";s.d(e,{IK:()=>z,Jq:()=>g,RA:()=>k,WQ:()=>B});var i,r=s(78403),n=s(27061);class h{constructor(t,e,s,i,r,n,h,o,a,l=0,c){this.p=t,this.stack=e,this.state=s,this.reducePos=i,this.pos=r,this.score=n,this.buffer=h,this.bufferBase=o,this.curContext=a,this.lookAhead=l,this.parent=c}toString(){return`[${this.stack.filter(((t,e)=>e%3==0)).concat(this.state)}]@${this.pos}${this.score?"!"+this.score:""}`}static start(t,e,s=0){let i=t.parser.context;return new h(t,[],e,s,s,0,[],0,i?new o(i,i.start):null,0,null)}get context(){return this.curContext?this.curContext.context:null}pushState(t,e){this.stack.push(this.state,e,this.bufferBase+this.buffer.length),this.state=t}reduce(t){var e;let s=t>>19,i=65535&t,{parser:r}=this.p,n=r.dynamicPrecedence(i);if(n&&(this.score+=n),0==s)return this.pushState(r.getGoto(this.state,i,!0),this.reducePos),i<r.minRepeatTerm&&this.storeNode(i,this.reducePos,this.reducePos,4,!0),void this.reduceContext(i,this.reducePos);let h=this.stack.length-3*(s-1)-(262144&t?6:0),o=h?this.stack[h-2]:this.p.ranges[0].from,a=this.reducePos-o;a>=2e3&&!(null===(e=this.p.parser.nodeSet.types[i])||void 0===e?void 0:e.isAnonymous)&&(o==this.p.lastBigReductionStart?(this.p.bigReductionCount++,this.p.lastBigReductionSize=a):this.p.lastBigReductionSize<a&&(this.p.bigReductionCount=1,this.p.lastBigReductionStart=o,this.p.lastBigReductionSize=a));let l=h?this.stack[h-1]:0,c=this.bufferBase+this.buffer.length-l;if(i<r.minRepeatTerm||131072&t){let t=r.stateFlag(this.state,1)?this.pos:this.reducePos;this.storeNode(i,o,t,c+4,!0)}if(262144&t)this.state=this.stack[h];else{let t=this.stack[h-3];this.state=r.getGoto(t,i,!0)}for(;this.stack.length>h;)this.stack.pop();this.reduceContext(i,o)}storeNode(t,e,s,i=4,r=!1){if(0==t&&(!this.stack.length||this.stack[this.stack.length-1]<this.buffer.length+this.bufferBase)){let t=this,i=this.buffer.length;if(0==i&&t.parent&&(i=t.bufferBase-t.parent.bufferBase,t=t.parent),i>0&&0==t.buffer[i-4]&&t.buffer[i-1]>-1){if(e==s)return;if(t.buffer[i-2]>=e)return void(t.buffer[i-2]=s)}}if(r&&this.pos!=s){let r=this.buffer.length;if(r>0&&0!=this.buffer[r-4])for(;r>0&&this.buffer[r-2]>s;)this.buffer[r]=this.buffer[r-4],this.buffer[r+1]=this.buffer[r-3],this.buffer[r+2]=this.buffer[r-2],this.buffer[r+3]=this.buffer[r-1],r-=4,i>4&&(i-=4);this.buffer[r]=t,this.buffer[r+1]=e,this.buffer[r+2]=s,this.buffer[r+3]=i}else this.buffer.push(t,e,s,i)}shift(t,e,s){let i=this.pos;if(131072&t)this.pushState(65535&t,this.pos);else if(0==(262144&t)){let r=t,{parser:n}=this.p;(s>this.pos||e<=n.maxNode)&&(this.pos=s,n.stateFlag(r,1)||(this.reducePos=s)),this.pushState(r,i),this.shiftContext(e,i),e<=n.maxNode&&this.buffer.push(e,i,s,4)}else this.pos=s,this.shiftContext(e,i),e<=this.p.parser.maxNode&&this.buffer.push(e,i,s,4)}apply(t,e,s){65536&t?this.reduce(t):this.shift(t,e,s)}useNode(t,e){let s=this.p.reused.length-1;(s<0||this.p.reused[s]!=t)&&(this.p.reused.push(t),s++);let i=this.pos;this.reducePos=this.pos=i+t.length,this.pushState(e,i),this.buffer.push(s,i,this.reducePos,-1),this.curContext&&this.updateContext(this.curContext.tracker.reuse(this.curContext.context,t,this,this.p.stream.reset(this.pos-t.length)))}split(){let t=this,e=t.buffer.length;for(;e>0&&t.buffer[e-2]>t.reducePos;)e-=4;let s=t.buffer.slice(e),i=t.bufferBase+e;for(;t&&i==t.bufferBase;)t=t.parent;return new h(this.p,this.stack.slice(),this.state,this.reducePos,this.pos,this.score,s,i,this.curContext,this.lookAhead,t)}recoverByDelete(t,e){let s=t<=this.p.parser.maxNode;s&&this.storeNode(t,this.pos,e,4),this.storeNode(0,this.pos,e,s?8:4),this.pos=this.reducePos=e,this.score-=190}canShift(t){for(let e=new a(this);;){let s=this.p.parser.stateSlot(e.state,4)||this.p.parser.hasAction(e.state,t);if(0==s)return!1;if(0==(65536&s))return!0;e.reduce(s)}}recoverByInsert(t){if(this.stack.length>=300)return[];let e=this.p.parser.nextStates(this.state);if(e.length>8||this.stack.length>=120){let s=[];for(let i,r=0;r<e.length;r+=2)(i=e[r+1])!=this.state&&this.p.parser.hasAction(i,t)&&s.push(e[r],i);if(this.stack.length<120)for(let t=0;s.length<8&&t<e.length;t+=2){let i=e[t+1];s.some(((t,e)=>1&e&&t==i))||s.push(e[t],i)}e=s}let s=[];for(let t=0;t<e.length&&s.length<4;t+=2){let i=e[t+1];if(i==this.state)continue;let r=this.split();r.pushState(i,this.pos),r.storeNode(0,r.pos,r.pos,4,!0),r.shiftContext(e[t],this.pos),r.score-=200,s.push(r)}return s}forceReduce(){let{parser:t}=this.p,e=t.stateSlot(this.state,5);if(0==(65536&e))return!1;if(!t.validAction(this.state,e)){let s=e>>19,i=65535&e,r=this.stack.length-3*s;if(r<0||t.getGoto(this.stack[r],i,!1)<0){let t=this.findForcedReduction();if(null==t)return!1;e=t}this.storeNode(0,this.pos,this.pos,4,!0),this.score-=100}return this.reducePos=this.pos,this.reduce(e),!0}findForcedReduction(){let{parser:t}=this.p,e=[],s=(i,r)=>{if(!e.includes(i))return e.push(i),t.allActions(i,(e=>{if(393216&e);else if(65536&e){let s=(e>>19)-r;if(s>1){let i=65535&e,r=this.stack.length-3*s;if(r>=0&&t.getGoto(this.stack[r],i,!1)>=0)return s<<19|65536|i}}else{let t=s(e,r+1);if(null!=t)return t}}))};return s(this.state,0)}forceAll(){for(;!this.p.parser.stateFlag(this.state,2);)if(!this.forceReduce()){this.storeNode(0,this.pos,this.pos,4,!0);break}return this}get deadEnd(){if(3!=this.stack.length)return!1;let{parser:t}=this.p;return 65535==t.data[t.stateSlot(this.state,1)]&&!t.stateSlot(this.state,4)}restart(){this.state=this.stack[0],this.stack.length=0}sameState(t){if(this.state!=t.state||this.stack.length!=t.stack.length)return!1;for(let e=0;e<this.stack.length;e+=3)if(this.stack[e]!=t.stack[e])return!1;return!0}get parser(){return this.p.parser}dialectEnabled(t){return this.p.parser.dialect.flags[t]}shiftContext(t,e){this.curContext&&this.updateContext(this.curContext.tracker.shift(this.curContext.context,t,this,this.p.stream.reset(e)))}reduceContext(t,e){this.curContext&&this.updateContext(this.curContext.tracker.reduce(this.curContext.context,t,this,this.p.stream.reset(e)))}emitContext(){let t=this.buffer.length-1;(t<0||-3!=this.buffer[t])&&this.buffer.push(this.curContext.hash,this.pos,this.pos,-3)}emitLookAhead(){let t=this.buffer.length-1;(t<0||-4!=this.buffer[t])&&this.buffer.push(this.lookAhead,this.pos,this.pos,-4)}updateContext(t){if(t!=this.curContext.context){let e=new o(this.curContext.tracker,t);e.hash!=this.curContext.hash&&this.emitContext(),this.curContext=e}}setLookAhead(t){t>this.lookAhead&&(this.emitLookAhead(),this.lookAhead=t)}close(){this.curContext&&this.curContext.tracker.strict&&this.emitContext(),this.lookAhead>0&&this.emitLookAhead()}}class o{constructor(t,e){this.tracker=t,this.context=e,this.hash=t.strict?t.hash(e):0}}!function(t){t[t.Insert=200]="Insert",t[t.Delete=190]="Delete",t[t.Reduce=100]="Reduce",t[t.MaxNext=4]="MaxNext",t[t.MaxInsertStackDepth=300]="MaxInsertStackDepth",t[t.DampenInsertStackDepth=120]="DampenInsertStackDepth",t[t.MinBigReduction=2e3]="MinBigReduction"}(i||(i={}));class a{constructor(t){this.start=t,this.state=t.state,this.stack=t.stack,this.base=this.stack.length}reduce(t){let e=65535&t,s=t>>19;0==s?(this.stack==this.start.stack&&(this.stack=this.stack.slice()),this.stack.push(this.state,0,0),this.base+=3):this.base-=3*(s-1);let i=this.start.p.parser.getGoto(this.stack[this.base-3],e,!0);this.state=i}}class l{constructor(t,e,s){this.stack=t,this.pos=e,this.index=s,this.buffer=t.buffer,0==this.index&&this.maybeNext()}static create(t,e=t.bufferBase+t.buffer.length){return new l(t,e,e-t.bufferBase)}maybeNext(){let t=this.stack.parent;null!=t&&(this.index=this.stack.bufferBase-t.bufferBase,this.stack=t,this.buffer=t.buffer)}get id(){return this.buffer[this.index-4]}get start(){return this.buffer[this.index-3]}get end(){return this.buffer[this.index-2]}get size(){return this.buffer[this.index-1]}next(){this.index-=4,this.pos-=4,0==this.index&&this.maybeNext()}fork(){return new l(this.stack,this.pos,this.index)}}function c(t,e=Uint16Array){if("string"!=typeof t)return t;let s=null;for(let i=0,r=0;i<t.length;){let n=0;for(;;){let e=t.charCodeAt(i++),s=!1;if(126==e){n=65535;break}e>=92&&e--,e>=34&&e--;let r=e-32;if(r>=46&&(r-=46,s=!0),n+=r,s)break;n*=46}s?s[r++]=n:s=new e(n)}return s}class u{constructor(){this.start=-1,this.value=-1,this.end=-1,this.extended=-1,this.lookAhead=0,this.mask=0,this.context=0}}const f=new u;class p{constructor(t,e){this.input=t,this.ranges=e,this.chunk="",this.chunkOff=0,this.chunk2="",this.chunk2Pos=0,this.next=-1,this.token=f,this.rangeIndex=0,this.pos=this.chunkPos=e[0].from,this.range=e[0],this.end=e[e.length-1].to,this.readNext()}resolveOffset(t,e){let s=this.range,i=this.rangeIndex,r=this.pos+t;for(;r<s.from;){if(!i)return null;let t=this.ranges[--i];r-=s.from-t.to,s=t}for(;e<0?r>s.to:r>=s.to;){if(i==this.ranges.length-1)return null;let t=this.ranges[++i];r+=t.from-s.to,s=t}return r}clipPos(t){if(t>=this.range.from&&t<this.range.to)return t;for(let e of this.ranges)if(e.to>t)return Math.max(t,e.from);return this.end}peek(t){let e,s,i=this.chunkOff+t;if(i>=0&&i<this.chunk.length)e=this.pos+t,s=this.chunk.charCodeAt(i);else{let i=this.resolveOffset(t,1);if(null==i)return-1;if(e=i,e>=this.chunk2Pos&&e<this.chunk2Pos+this.chunk2.length)s=this.chunk2.charCodeAt(e-this.chunk2Pos);else{let t=this.rangeIndex,i=this.range;for(;i.to<=e;)i=this.ranges[++t];this.chunk2=this.input.chunk(this.chunk2Pos=e),e+this.chunk2.length>i.to&&(this.chunk2=this.chunk2.slice(0,i.to-e)),s=this.chunk2.charCodeAt(0)}}return e>=this.token.lookAhead&&(this.token.lookAhead=e+1),s}acceptToken(t,e=0){let s=e?this.resolveOffset(e,-1):this.pos;if(null==s||s<this.token.start)throw new RangeError("Token end out of bounds");this.token.value=t,this.token.end=s}getChunk(){if(this.pos>=this.chunk2Pos&&this.pos<this.chunk2Pos+this.chunk2.length){let{chunk:t,chunkPos:e}=this;this.chunk=this.chunk2,this.chunkPos=this.chunk2Pos,this.chunk2=t,this.chunk2Pos=e,this.chunkOff=this.pos-this.chunkPos}else{this.chunk2=this.chunk,this.chunk2Pos=this.chunkPos;let t=this.input.chunk(this.pos),e=this.pos+t.length;this.chunk=e>this.range.to?t.slice(0,this.range.to-this.pos):t,this.chunkPos=this.pos,this.chunkOff=0}}readNext(){return this.chunkOff>=this.chunk.length&&(this.getChunk(),this.chunkOff==this.chunk.length)?this.next=-1:this.next=this.chunk.charCodeAt(this.chunkOff)}advance(t=1){for(this.chunkOff+=t;this.pos+t>=this.range.to;){if(this.rangeIndex==this.ranges.length-1)return this.setDone();t-=this.range.to-this.pos,this.range=this.ranges[++this.rangeIndex],this.pos=this.range.from}return this.pos+=t,this.pos>=this.token.lookAhead&&(this.token.lookAhead=this.pos+1),this.readNext()}setDone(){return this.pos=this.chunkPos=this.end,this.range=this.ranges[this.rangeIndex=this.ranges.length-1],this.chunk="",this.next=-1}reset(t,e){if(e?(this.token=e,e.start=t,e.lookAhead=t+1,e.value=e.extended=-1):this.token=f,this.pos!=t){if(this.pos=t,t==this.end)return this.setDone(),this;for(;t<this.range.from;)this.range=this.ranges[--this.rangeIndex];for(;t>=this.range.to;)this.range=this.ranges[++this.rangeIndex];t>=this.chunkPos&&t<this.chunkPos+this.chunk.length?this.chunkOff=t-this.chunkPos:(this.chunk="",this.chunkOff=0),this.readNext()}return this}read(t,e){if(t>=this.chunkPos&&e<=this.chunkPos+this.chunk.length)return this.chunk.slice(t-this.chunkPos,e-this.chunkPos);if(t>=this.chunk2Pos&&e<=this.chunk2Pos+this.chunk2.length)return this.chunk2.slice(t-this.chunk2Pos,e-this.chunk2Pos);if(t>=this.range.from&&e<=this.range.to)return this.input.read(t,e);let s="";for(let i of this.ranges){if(i.from>=e)break;i.to>t&&(s+=this.input.read(Math.max(i.from,t),Math.min(i.to,e)))}return s}}class d{constructor(t,e){this.data=t,this.id=e}token(t,e){let{parser:s}=e.p;m(this.data,t,e,this.id,s.data,s.tokenPrecTable)}}d.prototype.contextual=d.prototype.fallback=d.prototype.extend=!1;class k{constructor(t,e,s){this.precTable=e,this.elseToken=s,this.data="string"==typeof t?c(t):t}token(t,e){let s=t.pos,i=0;for(;;){let s=t.next<0,r=t.resolveOffset(1,1);if(m(this.data,t,e,0,this.data,this.precTable),t.token.value>-1)break;if(null==this.elseToken)return;if(s||i++,null==r)break;t.reset(r,t.token)}i&&(t.reset(s,t.token),t.acceptToken(this.elseToken,i))}}k.prototype.contextual=d.prototype.fallback=d.prototype.extend=!1;class g{constructor(t,e={}){this.token=t,this.contextual=!!e.contextual,this.fallback=!!e.fallback,this.extend=!!e.extend}}function m(t,e,s,i,r,n){let h=0,o=1<<i,{dialect:a}=s.p.parser;t:for(;0!=(o&t[h]);){let s=t[h+1];for(let i=h+3;i<s;i+=2)if((t[i+1]&o)>0){let s=t[i];if(a.allows(s)&&(-1==e.token.value||e.token.value==s||b(s,e.token.value,r,n))){e.acceptToken(s);break}}let i=e.next,l=0,c=t[h+2];if(!(e.next<0&&c>l&&65535==t[s+3*c-3]&&65535==t[s+3*c-3])){for(;l<c;){let r=l+c>>1,n=s+r+(r<<1),o=t[n],a=t[n+1]||65536;if(i<o)c=r;else{if(!(i>=a)){h=t[n+2],e.advance();continue t}l=r+1}}break}h=t[s+3*c-1]}}function x(t,e,s){for(let i,r=e;65535!=(i=t[r]);r++)if(i==s)return r-e;return-1}function b(t,e,s,i){let r=x(s,i,e);return r<0||x(s,i,t)<r}const v=void 0!==n&&n.env&&/\bparse\b/.test(n.env.LOG);let S=null;var T,P;function A(t,e,s){let i=t.cursor(r.IterMode.IncludeAnonymous);for(i.moveTo(e);;)if(!(s<0?i.childBefore(e):i.childAfter(e)))for(;;){if((s<0?i.to<e:i.from>e)&&!i.type.isError)return s<0?Math.max(0,Math.min(i.to-1,e-25)):Math.min(t.length,Math.max(i.from+1,e+25));if(s<0?i.prevSibling():i.nextSibling())break;if(!i.parent())return s<0?0:t.length}}!function(t){t[t.Margin=25]="Margin"}(T||(T={}));class C{constructor(t,e){this.fragments=t,this.nodeSet=e,this.i=0,this.fragment=null,this.safeFrom=-1,this.safeTo=-1,this.trees=[],this.start=[],this.index=[],this.nextFragment()}nextFragment(){let t=this.fragment=this.i==this.fragments.length?null:this.fragments[this.i++];if(t){for(this.safeFrom=t.openStart?A(t.tree,t.from+t.offset,1)-t.offset:t.from,this.safeTo=t.openEnd?A(t.tree,t.to+t.offset,-1)-t.offset:t.to;this.trees.length;)this.trees.pop(),this.start.pop(),this.index.pop();this.trees.push(t.tree),this.start.push(-t.offset),this.index.push(0),this.nextStart=this.safeFrom}else this.nextStart=1e9}nodeAt(t){if(t<this.nextStart)return null;for(;this.fragment&&this.safeTo<=t;)this.nextFragment();if(!this.fragment)return null;for(;;){let e=this.trees.length-1;if(e<0)return this.nextFragment(),null;let s=this.trees[e],i=this.index[e];if(i==s.children.length){this.trees.pop(),this.start.pop(),this.index.pop();continue}let n=s.children[i],h=this.start[e]+s.positions[i];if(h>t)return this.nextStart=h,null;if(n instanceof r.Tree){if(h==t){if(h<this.safeFrom)return null;let t=h+n.length;if(t<=this.safeTo){let e=n.prop(r.NodeProp.lookAhead);if(!e||t+e<this.fragment.to)return n}}this.index[e]++,h+n.length>=Math.max(this.safeFrom,t)&&(this.trees.push(n),this.start.push(h),this.index.push(0))}else this.index[e]++,this.nextStart=h+n.length}}}class y{constructor(t,e){this.stream=e,this.tokens=[],this.mainToken=null,this.actions=[],this.tokens=t.tokenizers.map((t=>new u))}getActions(t){let e=0,s=null,{parser:i}=t.p,{tokenizers:r}=i,n=i.stateSlot(t.state,3),h=t.curContext?t.curContext.hash:0,o=0;for(let i=0;i<r.length;i++){if(0==(1<<i&n))continue;let a=r[i],l=this.tokens[i];if((!s||a.fallback)&&((a.contextual||l.start!=t.pos||l.mask!=n||l.context!=h)&&(this.updateCachedToken(l,a,t),l.mask=n,l.context=h),l.lookAhead>l.end+25&&(o=Math.max(l.lookAhead,o)),0!=l.value)){let i=e;if(l.extended>-1&&(e=this.addActions(t,l.extended,l.end,e)),e=this.addActions(t,l.value,l.end,e),!a.extend&&(s=l,e>i))break}}for(;this.actions.length>e;)this.actions.pop();return o&&t.setLookAhead(o),s||t.pos!=this.stream.end||(s=new u,s.value=t.p.parser.eofTerm,s.start=s.end=t.pos,e=this.addActions(t,s.value,s.end,e)),this.mainToken=s,this.actions}getMainToken(t){if(this.mainToken)return this.mainToken;let e=new u,{pos:s,p:i}=t;return e.start=s,e.end=Math.min(s+1,i.stream.end),e.value=s==i.stream.end?i.parser.eofTerm:0,e}updateCachedToken(t,e,s){let i=this.stream.clipPos(s.pos);if(e.token(this.stream.reset(i,t),s),t.value>-1){let{parser:e}=s.p;for(let i=0;i<e.specialized.length;i++)if(e.specialized[i]==t.value){let r=e.specializers[i](this.stream.read(t.start,t.end),s);if(r>=0&&s.p.parser.dialect.allows(r>>1)){0==(1&r)?t.value=r>>1:t.extended=r>>1;break}}}else t.value=0,t.end=this.stream.clipPos(i+1)}putAction(t,e,s,i){for(let e=0;e<i;e+=3)if(this.actions[e]==t)return i;return this.actions[i++]=t,this.actions[i++]=e,this.actions[i++]=s,i}addActions(t,e,s,i){let{state:r}=t,{parser:n}=t.p,{data:h}=n;for(let t=0;t<2;t++)for(let o=n.stateSlot(r,t?2:1);;o+=3){if(65535==h[o]){if(1!=h[o+1]){0==i&&2==h[o+1]&&(i=this.putAction(I(h,o+2),e,s,i));break}o=I(h,o+2)}h[o]==e&&(i=this.putAction(I(h,o+1),e,s,i))}return i}}!function(t){t[t.Distance=5]="Distance",t[t.MaxRemainingPerStep=3]="MaxRemainingPerStep",t[t.MinBufferLengthPrune=500]="MinBufferLengthPrune",t[t.ForceReduceLimit=10]="ForceReduceLimit",t[t.CutDepth=15e3]="CutDepth",t[t.CutTo=9e3]="CutTo",t[t.MaxLeftAssociativeReductionCount=300]="MaxLeftAssociativeReductionCount",t[t.MaxStackCount=12]="MaxStackCount"}(P||(P={}));class w{constructor(t,e,s,i){this.parser=t,this.input=e,this.ranges=i,this.recovering=0,this.nextStackID=9812,this.minStackPos=0,this.reused=[],this.stoppedAt=null,this.lastBigReductionStart=-1,this.lastBigReductionSize=0,this.bigReductionCount=0,this.stream=new p(e,i),this.tokens=new y(t,this.stream),this.topTerm=t.top[1];let{from:r}=i[0];this.stacks=[h.start(this,t.top[0],r)],this.fragments=s.length&&this.stream.end-r>4*t.bufferLength?new C(s,t.nodeSet):null}get parsedPos(){return this.minStackPos}advance(){let t,e,s=this.stacks,i=this.minStackPos,r=this.stacks=[];if(this.bigReductionCount>300&&1==s.length){let[t]=s;for(;t.forceReduce()&&t.stack.length&&t.stack[t.stack.length-2]>=this.lastBigReductionStart;);this.bigReductionCount=this.lastBigReductionSize=0}for(let n=0;n<s.length;n++){let h=s[n];for(;;){if(this.tokens.mainToken=null,h.pos>i)r.push(h);else{if(this.advanceStack(h,r,s))continue;{t||(t=[],e=[]),t.push(h);let s=this.tokens.getMainToken(h);e.push(s.value,s.end)}}break}}if(!r.length){let e=t&&function(t){let e=null;for(let s of t){let t=s.p.stoppedAt;(s.pos==s.p.stream.end||null!=t&&s.pos>t)&&s.p.parser.stateFlag(s.state,2)&&(!e||e.score<s.score)&&(e=s)}return e}(t);if(e)return this.stackToTree(e);if(this.parser.strict)throw v&&t&&console.log("Stuck with token "+(this.tokens.mainToken?this.parser.getName(this.tokens.mainToken.value):"none")),new SyntaxError("No parse at "+i);this.recovering||(this.recovering=5)}if(this.recovering&&t){let s=null!=this.stoppedAt&&t[0].pos>this.stoppedAt?t[0]:this.runRecovery(t,e,r);if(s)return this.stackToTree(s.forceAll())}if(this.recovering){let t=1==this.recovering?1:3*this.recovering;if(r.length>t)for(r.sort(((t,e)=>e.score-t.score));r.length>t;)r.pop();r.some((t=>t.reducePos>i))&&this.recovering--}else if(r.length>1){t:for(let t=0;t<r.length-1;t++){let e=r[t];for(let s=t+1;s<r.length;s++){let i=r[s];if(e.sameState(i)||e.buffer.length>500&&i.buffer.length>500){if(!((e.score-i.score||e.buffer.length-i.buffer.length)>0)){r.splice(t--,1);continue t}r.splice(s--,1)}}}r.length>12&&r.splice(12,r.length-12)}this.minStackPos=r[0].pos;for(let t=1;t<r.length;t++)r[t].pos<this.minStackPos&&(this.minStackPos=r[t].pos);return null}stopAt(t){if(null!=this.stoppedAt&&this.stoppedAt<t)throw new RangeError("Can't move stoppedAt forward");this.stoppedAt=t}advanceStack(t,e,s){let i=t.pos,{parser:n}=this,h=v?this.stackID(t)+" -> ":"";if(null!=this.stoppedAt&&i>this.stoppedAt)return t.forceReduce()?t:null;if(this.fragments){let e=t.curContext&&t.curContext.tracker.strict,s=e?t.curContext.hash:0;for(let o=this.fragments.nodeAt(i);o;){let i=this.parser.nodeSet.types[o.type.id]==o.type?n.getGoto(t.state,o.type.id):-1;if(i>-1&&o.length&&(!e||(o.prop(r.NodeProp.contextHash)||0)==s))return t.useNode(o,i),v&&console.log(h+this.stackID(t)+` (via reuse of ${n.getName(o.type.id)})`),!0;if(!(o instanceof r.Tree)||0==o.children.length||o.positions[0]>0)break;let a=o.children[0];if(!(a instanceof r.Tree&&0==o.positions[0]))break;o=a}}let o=n.stateSlot(t.state,4);if(o>0)return t.reduce(o),v&&console.log(h+this.stackID(t)+` (via always-reduce ${n.getName(65535&o)})`),!0;if(t.stack.length>=15e3)for(;t.stack.length>9e3&&t.forceReduce(););let a=this.tokens.getActions(t);for(let r=0;r<a.length;){let o=a[r++],l=a[r++],c=a[r++],u=r==a.length||!s,f=u?t:t.split();if(f.apply(o,l,c),v&&console.log(h+this.stackID(f)+` (via ${0==(65536&o)?"shift":`reduce of ${n.getName(65535&o)}`} for ${n.getName(l)} @ ${i}${f==t?"":", split"})`),u)return!0;f.pos>i?e.push(f):s.push(f)}return!1}advanceFully(t,e){let s=t.pos;for(;;){if(!this.advanceStack(t,null,null))return!1;if(t.pos>s)return R(t,e),!0}}runRecovery(t,e,s){let i=null,r=!1;for(let n=0;n<t.length;n++){let h=t[n],o=e[n<<1],a=e[1+(n<<1)],l=v?this.stackID(h)+" -> ":"";if(h.deadEnd){if(r)continue;if(r=!0,h.restart(),v&&console.log(l+this.stackID(h)+" (restarted)"),this.advanceFully(h,s))continue}let c=h.split(),u=l;for(let t=0;c.forceReduce()&&t<10&&(v&&console.log(u+this.stackID(c)+" (via force-reduce)"),!this.advanceFully(c,s));t++)v&&(u=this.stackID(c)+" -> ");for(let t of h.recoverByInsert(o))v&&console.log(l+this.stackID(t)+" (via recover-insert)"),this.advanceFully(t,s);this.stream.end>h.pos?(a==h.pos&&(a++,o=0),h.recoverByDelete(o,a),v&&console.log(l+this.stackID(h)+` (via recover-delete ${this.parser.getName(o)})`),R(h,s)):(!i||i.score<h.score)&&(i=h)}return i}stackToTree(t){return t.close(),r.Tree.build({buffer:l.create(t),nodeSet:this.parser.nodeSet,topID:this.topTerm,maxBufferLength:this.parser.bufferLength,reused:this.reused,start:this.ranges[0].from,length:t.pos-this.ranges[0].from,minRepeatType:this.parser.minRepeatTerm})}stackID(t){let e=(S||(S=new WeakMap)).get(t);return e||S.set(t,e=String.fromCodePoint(this.nextStackID++)),e+t}}function R(t,e){for(let s=0;s<e.length;s++){let i=e[s];if(i.pos==t.pos&&i.sameState(t))return void(e[s].score<t.score&&(e[s]=t))}e.push(t)}class N{constructor(t,e,s){this.source=t,this.flags=e,this.disabled=s}allows(t){return!this.disabled||0==this.disabled[t]}}const D=t=>t;class z{constructor(t){this.start=t.start,this.shift=t.shift||D,this.reduce=t.reduce||D,this.reuse=t.reuse||D,this.hash=t.hash||(()=>0),this.strict=!1!==t.strict}}class B extends r.Parser{constructor(t){if(super(),this.wrappers=[],14!=t.version)throw new RangeError(`Parser version (${t.version}) doesn't match runtime version (14)`);let e=t.nodeNames.split(" ");this.minRepeatTerm=e.length;for(let s=0;s<t.repeatNodeCount;s++)e.push("");let s=Object.keys(t.topRules).map((e=>t.topRules[e][1])),i=[];for(let t=0;t<e.length;t++)i.push([]);function n(t,e,s){i[t].push([e,e.deserialize(String(s))])}if(t.nodeProps)for(let e of t.nodeProps){let t=e[0];"string"==typeof t&&(t=r.NodeProp[t]);for(let s=1;s<e.length;){let i=e[s++];if(i>=0)n(i,t,e[s++]);else{let r=e[s+-i];for(let h=-i;h>0;h--)n(e[s++],t,r);s++}}}this.nodeSet=new r.NodeSet(e.map(((e,n)=>r.NodeType.define({name:n>=this.minRepeatTerm?void 0:e,id:n,props:i[n],top:s.indexOf(n)>-1,error:0==n,skipped:t.skippedNodes&&t.skippedNodes.indexOf(n)>-1})))),t.propSources&&(this.nodeSet=this.nodeSet.extend(...t.propSources)),this.strict=!1,this.bufferLength=r.DefaultBufferLength;let h=c(t.tokenData);this.context=t.context,this.specializerSpecs=t.specialized||[],this.specialized=new Uint16Array(this.specializerSpecs.length);for(let t=0;t<this.specializerSpecs.length;t++)this.specialized[t]=this.specializerSpecs[t].term;this.specializers=this.specializerSpecs.map(M),this.states=c(t.states,Uint32Array),this.data=c(t.stateData),this.goto=c(t.goto),this.maxTerm=t.maxTerm,this.tokenizers=t.tokenizers.map((t=>"number"==typeof t?new d(h,t):t)),this.topRules=t.topRules,this.dialects=t.dialects||{},this.dynamicPrecedences=t.dynamicPrecedences||null,this.tokenPrecTable=t.tokenPrec,this.termNames=t.termNames||null,this.maxNode=this.nodeSet.types.length-1,this.dialect=this.parseDialect(),this.top=this.topRules[Object.keys(this.topRules)[0]]}createParse(t,e,s){let i=new w(this,t,e,s);for(let r of this.wrappers)i=r(i,t,e,s);return i}getGoto(t,e,s=!1){let i=this.goto;if(e>=i[0])return-1;for(let r=i[e+1];;){let e=i[r++],n=1&e,h=i[r++];if(n&&s)return h;for(let s=r+(e>>1);r<s;r++)if(i[r]==t)return h;if(n)return-1}}hasAction(t,e){let s=this.data;for(let i=0;i<2;i++)for(let r,n=this.stateSlot(t,i?2:1);;n+=3){if(65535==(r=s[n])){if(1!=s[n+1]){if(2==s[n+1])return I(s,n+2);break}r=s[n=I(s,n+2)]}if(r==e||0==r)return I(s,n+1)}return 0}stateSlot(t,e){return this.states[6*t+e]}stateFlag(t,e){return(this.stateSlot(t,0)&e)>0}validAction(t,e){return!!this.allActions(t,(t=>t==e||null))}allActions(t,e){let s=this.stateSlot(t,4),i=s?e(s):void 0;for(let s=this.stateSlot(t,1);null==i;s+=3){if(65535==this.data[s]){if(1!=this.data[s+1])break;s=I(this.data,s+2)}i=e(I(this.data,s+1))}return i}nextStates(t){let e=[];for(let s=this.stateSlot(t,1);;s+=3){if(65535==this.data[s]){if(1!=this.data[s+1])break;s=I(this.data,s+2)}if(0==(1&this.data[s+2])){let t=this.data[s+1];e.some(((e,s)=>1&s&&e==t))||e.push(this.data[s],t)}}return e}configure(t){let e=Object.assign(Object.create(B.prototype),this);if(t.props&&(e.nodeSet=this.nodeSet.extend(...t.props)),t.top){let s=this.topRules[t.top];if(!s)throw new RangeError(`Invalid top rule name ${t.top}`);e.top=s}return t.tokenizers&&(e.tokenizers=this.tokenizers.map((e=>{let s=t.tokenizers.find((t=>t.from==e));return s?s.to:e}))),t.specializers&&(e.specializers=this.specializers.slice(),e.specializerSpecs=this.specializerSpecs.map(((s,i)=>{let r=t.specializers.find((t=>t.from==s.external));if(!r)return s;let n=Object.assign(Object.assign({},s),{external:r.to});return e.specializers[i]=M(n),n}))),t.contextTracker&&(e.context=t.contextTracker),t.dialect&&(e.dialect=this.parseDialect(t.dialect)),null!=t.strict&&(e.strict=t.strict),t.wrap&&(e.wrappers=e.wrappers.concat(t.wrap)),null!=t.bufferLength&&(e.bufferLength=t.bufferLength),e}hasWrappers(){return this.wrappers.length>0}getName(t){return this.termNames?this.termNames[t]:String(t<=this.maxNode&&this.nodeSet.types[t].name||t)}get eofTerm(){return this.maxNode+1}get topNode(){return this.nodeSet.types[this.top[1]]}dynamicPrecedence(t){let e=this.dynamicPrecedences;return null==e?0:e[t]||0}parseDialect(t){let e=Object.keys(this.dialects),s=e.map((()=>!1));if(t)for(let i of t.split(" ")){let t=e.indexOf(i);t>=0&&(s[t]=!0)}let i=null;for(let t=0;t<e.length;t++)if(!s[t])for(let s,r=this.dialects[e[t]];65535!=(s=this.data[r++]);)(i||(i=new Uint8Array(this.maxTerm+1)))[s]=1;return new N(t,s,i)}static deserialize(t){return new B(t)}}function I(t,e){return t[e]|t[e+1]<<16}function M(t){if(t.external){let e=t.extend?1:0;return(s,i)=>t.external(s,i)<<1|e}return t.get}},27061:t=>{var e,s,i=t.exports={};function r(){throw new Error("setTimeout has not been defined")}function n(){throw new Error("clearTimeout has not been defined")}function h(t){if(e===setTimeout)return setTimeout(t,0);if((e===r||!e)&&setTimeout)return e=setTimeout,setTimeout(t,0);try{return e(t,0)}catch(s){try{return e.call(null,t,0)}catch(s){return e.call(this,t,0)}}}!function(){try{e="function"==typeof setTimeout?setTimeout:r}catch(t){e=r}try{s="function"==typeof clearTimeout?clearTimeout:n}catch(t){s=n}}();var o,a=[],l=!1,c=-1;function u(){l&&o&&(l=!1,o.length?a=o.concat(a):c=-1,a.length&&f())}function f(){if(!l){var t=h(u);l=!0;for(var e=a.length;e;){for(o=a,a=[];++c<e;)o&&o[c].run();c=-1,e=a.length}o=null,l=!1,function(t){if(s===clearTimeout)return clearTimeout(t);if((s===n||!s)&&clearTimeout)return s=clearTimeout,clearTimeout(t);try{return s(t)}catch(e){try{return s.call(null,t)}catch(e){return s.call(this,t)}}}(t)}}function p(t,e){this.fun=t,this.array=e}function d(){}i.nextTick=function(t){var e=new Array(arguments.length-1);if(arguments.length>1)for(var s=1;s<arguments.length;s++)e[s-1]=arguments[s];a.push(new p(t,e)),1!==a.length||l||h(f)},p.prototype.run=function(){this.fun.apply(null,this.array)},i.title="browser",i.browser=!0,i.env={},i.argv=[],i.version="",i.versions={},i.on=d,i.addListener=d,i.once=d,i.off=d,i.removeListener=d,i.removeAllListeners=d,i.emit=d,i.prependListener=d,i.prependOnceListener=d,i.listeners=function(t){return[]},i.binding=function(t){throw new Error("process.binding is not supported")},i.cwd=function(){return"/"},i.chdir=function(t){throw new Error("process.chdir is not supported")},i.umask=function(){return 0}}}]);
//# sourceMappingURL=49906.7d14022.js.map