import re, json, openpyxl
from collections import defaultdict, deque

def clean(v): return None if v is None else str(v).strip()
def is_ph(v): return v is None or v.lower().startswith('i use') or v.lower()=='none'
def dint(t):
    m=re.search(r'Level (\d)',str(t)); return int(m.group(1)) if m else None
def yrs(v):
    try: return int(v)
    except: return None
XW={'Persistent Slab':'Persistent weak layers','Deep Persistent Slab':'Persistent weak layers',
    'Wet Slab':'Wet snow','Wet Loose':'Wet snow','Dry Loose':'New snow','Storm Slab':'New snow',
    'Wind Slab':'Wind-drifted snow','No Distinct Problem':'No distinct problem'}
EA={'Persistent Weak Layers':'Persistent weak layers','Wet Snow':'Wet snow','Wind Slab':'Wind-drifted snow',
    'New Snow':'New snow','No Distinct Problem':'No distinct problem','Gliding Snow':'Gliding snow'}
NA_COLS=[12,15,18,21,24,27,30,33,36,39]; EAWS_COLS=[13,16,19,22,25,28,31,34,37,40]; DCOLS=[11,14,17,20,23,26,29,32,35,38]

wb=openpyxl.load_workbook('/Users/coop/Downloads/2026_data.xlsx',read_only=True,data_only=True)
rows=[r for r in wb['Master Sheet'].iter_rows(values_only=True) if any(c is not None for c in r)][1:]
byKey=defaultdict(deque)
for r in rows:
    home_e=str(r[2]).strip()=='Europe'
    group='Europe' if home_e else 'NA/NZ'
    country=clean(r[3]) if home_e else clean(r[2])
    center=clean(r[4]) or clean(r[5]) or 'Unknown'
    S=[dint(r[c]) for c in DCOLS]
    P=[]
    for s in range(10):
        naV=clean(r[NA_COLS[s]]); eaV=clean(r[EAWS_COLS[s]])
        val=(eaV if not is_ph(eaV) else naV) if home_e else (naV if not is_ph(naV) else eaV)
        P.append(None if (val is None or is_ph(val)) else (EA.get(val) or XW.get(val)))
    byKey[(group,country,center,yrs(r[6]),tuple(S))].append(P)

raw=open('index.html').read()
line=[l for l in raw.splitlines() if 'const DATA =' in l][0]
i=line.find('const DATA ='); start=line.find('{',i)
depth=0;instr=False;esc=False;end=None
for j in range(start,len(line)):
    ch=line[j]
    if esc:esc=False;continue
    if ch=='\\':esc=True;continue
    if ch=='"':instr=not instr;continue
    if instr:continue
    if ch=='{':depth+=1
    elif ch=='}':
        depth-=1
        if depth==0:end=j;break
old_blob=line[start:end+1]
data=json.loads(old_blob)

assigned=0
for rec in data['records']:
    if rec['year']!=2026: continue
    key=(rec['group'],rec['country'],rec['center'],rec['years'],tuple(rec['S'+str(s)] for s in range(1,11)))
    if key not in byKey or not byKey[key]:
        raise SystemExit('NO MATCH for '+rec['id']+' '+str(key))
    P=byKey[key].popleft()
    for s in range(1,11): rec['P'+str(s)]=P[s-1]
    assigned+=1
leftover=sum(len(v) for v in byKey.values())
print('attached P to',assigned,'records; leftover:',leftover)
assert assigned==144 and leftover==0
raw=raw.replace(old_blob, json.dumps(data), 1)

html_anchor='  <div class="panel">\n    <h2>Reference: agreement benchmarks</h2>'
PANEL=r'''  <div class="panel">
    <h2>Avalanche problem &amp; danger by scenario (2026)</h2>
    <p class="sub">Each dot is one forecaster, placed at the primary avalanche problem they selected and colored by the danger level they assigned. Problems were collected in 2026 only, so this view uses 2026 respondents and follows every filter above.</p>
    <div id="probchart" style="height:660px"></div>
    <div class="legend">
      <span><span class="sw" style="background:var(--low)"></span>Low (1)</span>
      <span><span class="sw" style="background:var(--mod)"></span>Moderate (2)</span>
      <span><span class="sw" style="background:var(--con)"></span>Considerable (3)</span>
      <span><span class="sw" style="background:var(--high)"></span>High (4)</span>
      <span><span class="sw" style="background:var(--ext)"></span>Extreme (5)</span>
    </div>
    <details style="margin-top:12px">
      <summary class="sub" style="cursor:pointer">How the two problem systems were harmonized (field mapping)</summary>
      <p class="note">Respondents answered in one framework: North America and New Zealand used the North American problem types, Europe used the EAWS types. To compare them, the North American types were mapped onto the coarser EAWS set, so every dot is expressed in EAWS terms. EAWS answers pass through unchanged.</p>
      <table>
        <thead><tr><th>North American type</th><th>&rarr; EAWS term</th></tr></thead>
        <tbody>
          <tr><td>Persistent Slab, Deep Persistent Slab</td><td>Persistent weak layers</td></tr>
          <tr><td>Wet Slab, Wet Loose</td><td>Wet snow</td></tr>
          <tr><td>Storm Slab, Dry Loose</td><td>New snow</td></tr>
          <tr><td>Wind Slab</td><td>Wind-drifted snow</td></tr>
          <tr><td>No Distinct Problem</td><td>No distinct problem</td></tr>
        </tbody>
      </table>
      <p class="note">Gliding snow (EAWS) and Glide/Cornice (North American) were offered but never chosen, so nothing fell outside this mapping.</p>
    </details>
  </div>

'''
assert html_anchor in raw
raw=raw.replace(html_anchor, PANEL+html_anchor, 1)

JS=r'''const PROBCATS=['New snow','Wind-drifted snow','Persistent weak layers','Wet snow','No distinct problem'];
function renderProblems(records){
  const recs=records.filter(r=>r.year===2026 && r.P1!==undefined);
  if(!recs.length){ naMsg('probchart', state.year==='2016'
      ? 'Avalanche problems were collected in 2026 only. Set Year to 2026 or Both to see this chart.'
      : 'No 2026 respondents match the current filters.'); return; }
  const N=DATA.scenarios.length, xs=[],ys=[],cs=[],tx=[];
  for(let si=0; si<N; si++){
    const sc=DATA.scenarios[si];
    for(let ci=0; ci<PROBCATS.length; ci++){
      const cell=recs.filter(r=>r['P'+sc]===PROBCATS[ci]);
      cell.sort((a,b)=>(a['S'+sc]||9)-(b['S'+sc]||9));
      const n=cell.length; if(!n) continue;
      const ncols=Math.max(1,Math.ceil(Math.sqrt(n))), sp=0.82/Math.max(ncols,12), nrows=Math.ceil(n/ncols);
      cell.forEach((r,k)=>{
        const col=k%ncols, row=Math.floor(k/ncols), d=r['S'+sc];
        xs.push(ci+(col-(ncols-1)/2)*sp);
        ys.push((N-1-si)+(row-(nrows-1)/2)*sp);
        cs.push(LVCOLOR[d]||'#cccccc');
        tx.push('S'+sc+' • '+PROBCATS[ci]+'<br>danger: '+(d?LV[d]:'n/a')+'<br>'+effCountry(r)+' • '+r.center+'<br>'+(r.guidance_label||''));
      });
    }
  }
  Plotly.newPlot('probchart',[{x:xs,y:ys,mode:'markers',type:'scatter',
    marker:{size:9,color:cs,line:{color:'#fff',width:0.5}},text:tx,hoverinfo:'text'}],
   {margin:{t:10,r:10,b:96,l:36},
    xaxis:{tickvals:[0,1,2,3,4],ticktext:PROBCATS,range:[-0.7,4.7],tickangle:-18,zeroline:false,showgrid:true,gridcolor:'#eef0f2'},
    yaxis:{tickvals:DATA.scenarios.map((s,i)=>N-1-i),ticktext:DATA.scenarios.map(s=>'S'+s),range:[-0.7,N-0.3],zeroline:false,showgrid:false},
    font:{size:12},plot_bgcolor:'#fff'},
   {displayModeBar:false,responsive:true});
}

function rerender(){'''
assert 'function rerender(){' in raw
raw=raw.replace('function rerender(){', JS, 1)

hook='  renderGuid();\n  refreshNote(recs);'
assert hook in raw
raw=raw.replace(hook, '  renderGuid();\n  renderProblems(recs);\n  refreshNote(recs);', 1)

open('index.html','w').write(raw)
print('index.html updated OK')
