r"""Build a one-file browser recorder for the 80 owner takes (offline; nothing is uploaded).

    .\.venv\Scripts\python.exe scripts/make_owner_recorder.py
    -> var/owner_recorder.html   (open in Chrome; pick var/benchmark_audio/owner/takes as the folder)
"""
from __future__ import annotations

import json
from pathlib import Path

from register_owner_takes import parse_prompt_sheet

SHEET = Path("data/benchmarks/amount_v2/owner_prompt_sheet.md")
OUT = Path("var/owner_recorder.html")

PAGE = """<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Owner takes recorder</title>
<style>
body{font:18px system-ui;margin:0;padding:16px;max-width:520px;margin-inline:auto;background:#f3eee3;color:#222}
.card{background:#fff;border-radius:12px;padding:16px;margin:12px 0}h1{font-size:20px}
button{font:inherit;padding:14px 18px;border-radius:10px;border:0;background:#1b5e20;color:#fff;margin:4px 4px 4px 0;min-height:48px}
button.sec{background:#555}button.rec{background:#b71c1c}button:disabled{opacity:.4}
.id{font-weight:700}.meta{color:#555}progress{width:100%}
</style></head><body>
<h1>Owner takes — बोलकर रिकॉर्ड करें</h1>
<p class="meta">Say the estimate in your own words (dedh, dhai, saade, sava, barah sau…). Don't read it like a script.
Do it near a running scooter or fan. Nothing leaves this device.</p>
<div class="card"><button id="pick" class="sec">1. Choose folder (var/benchmark_audio/owner/takes)</button>
<div id="where" class="meta">No folder chosen — files will download instead.</div></div>
<div class="card"><div class="id" id="cid"></div><div id="items"></div><div id="delivery" class="meta"></div>
<progress id="bar" value="0" max="1"></progress><div id="count" class="meta"></div>
<div><button id="rec">● Record</button><button id="stop" class="rec" disabled>■ Stop</button>
<button id="play" class="sec" disabled>▶ Play</button><button id="save" disabled>Save &amp; next</button></div>
<div><button id="prev" class="sec">← Back</button><button id="skip" class="sec">Skip →</button></div>
<div id="status" class="meta"></div></div>
<script>
const CARDS=__CARDS__;
let i=0,dir=null,blob=null,rec=null,chunks=[],stream=null;
const $=id=>document.getElementById(id);
const done=new Set(JSON.parse(localStorage.getItem("ownerDone")||"[]"));
function show(){const c=CARDS[i];$("cid").textContent=c.id+(done.has(c.id)?"  ✓ saved":"");
 $("items").textContent="Items: "+c.items;$("delivery").textContent="Delivery: "+c.delivery;
 $("bar").max=CARDS.length;$("bar").value=done.size;$("count").textContent=done.size+" / "+CARDS.length+" saved";
 blob=null;$("play").disabled=$("save").disabled=true;$("status").textContent="";}
function wav(buf){const ch=buf.getChannelData(0),n=ch.length,out=new DataView(new ArrayBuffer(44+n*2));
 const w=(o,s)=>[...s].forEach((x,k)=>out.setUint8(o+k,x.charCodeAt(0)));
 w(0,"RIFF");out.setUint32(4,36+n*2,true);w(8,"WAVEfmt ");out.setUint32(16,16,true);out.setUint16(20,1,true);
 out.setUint16(22,1,true);out.setUint32(24,buf.sampleRate,true);out.setUint32(28,buf.sampleRate*2,true);
 out.setUint16(32,2,true);out.setUint16(34,16,true);w(36,"data");out.setUint32(40,n*2,true);
 for(let k=0;k<n;k++)out.setInt16(44+k*2,Math.max(-1,Math.min(1,ch[k]))*32767,true);
 return new Blob([out],{type:"audio/wav"});}
$("pick").onclick=async()=>{try{dir=await showDirectoryPicker({mode:"readwrite"});$("where").textContent="Saving into: "+dir.name;}
 catch(e){$("where").textContent="No folder — files will download.";}};
$("rec").onclick=async()=>{stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
 chunks=[];rec=new MediaRecorder(stream);rec.ondataavailable=e=>chunks.push(e.data);
 rec.onstop=async()=>{stream.getTracks().forEach(t=>t.stop());const ctx=new AudioContext();
  const buf=await ctx.decodeAudioData(await new Blob(chunks).arrayBuffer());blob=wav(buf);
  $("play").disabled=$("save").disabled=false;$("status").textContent=buf.duration.toFixed(1)+" s recorded";};
 rec.start();$("rec").disabled=true;$("stop").disabled=false;$("status").textContent="Recording…";};
$("stop").onclick=()=>{rec.stop();$("rec").disabled=false;$("stop").disabled=true;};
$("play").onclick=()=>new Audio(URL.createObjectURL(blob)).play();
$("save").onclick=async()=>{const c=CARDS[i],name=c.id+".wav";
 if(dir){const f=await dir.getFileHandle(name,{create:true});const w=await f.createWritable();await w.write(blob);await w.close();}
 else{const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;a.click();}
 done.add(c.id);localStorage.setItem("ownerDone",JSON.stringify([...done]));
 if(i<CARDS.length-1)i++;show();};
$("prev").onclick=()=>{i=Math.max(0,i-1);show()};$("skip").onclick=()=>{i=Math.min(CARDS.length-1,i+1);show()};
show();
</script></body></html>"""


def main() -> int:
    cards = [{"id": c["id"], "items": c["entities"]["items"], "delivery": c["entities"]["delivery"]} for c in parse_prompt_sheet(SHEET)]
    if len(cards) != 80:
        raise SystemExit(f"expected 80 cards, found {len(cards)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(PAGE.replace("__CARDS__", json.dumps(cards, ensure_ascii=False)), encoding="utf-8")
    print(f"wrote {OUT} ({len(cards)} cards)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
