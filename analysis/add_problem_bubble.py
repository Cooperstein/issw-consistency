raw=open('index.html').read()

html_anchor='  <div class="panel">\n    <h2>Reference: agreement benchmarks</h2>'
PANEL=r'''  <div class="panel">
    <h2>Primary problem consensus by scenario (2026)</h2>
    <p class="sub">Bubble size = the share of respondents who picked that problem for the scenario; color = problem type. This is the danger-free view of agreement on the problem itself. Follows every filter above; 2026 respondents only.</p>
    <div id="probbubble" style="height:560px"></div>
    <div class="legend">
      <span><span class="sw" style="background:#1b9e77"></span>New snow</span>
      <span><span class="sw" style="background:#7570b3"></span>Wind-drifted snow</span>
      <span><span class="sw" style="background:#d95f02"></span>Persistent weak layers</span>
      <span><span class="sw" style="background:#2b8cbe"></span>Wet snow</span>
      <span><span class="sw" style="background:#999999"></span>No distinct problem</span>
    </div>
  </div>

'''
assert html_anchor in raw
raw=raw.replace(html_anchor, PANEL+html_anchor, 1)

JS=r'''const PROBCOLOR={'New snow':'#1b9e77','Wind-drifted snow':'#7570b3','Persistent weak layers':'#d95f02','Wet snow':'#2b8cbe','No distinct problem':'#999999'};
function renderProblemBubble(records){
  const recs=records.filter(r=>r.year===2026 && r.P1!==undefined);
  if(!recs.length){ naMsg('probbubble', state.year==='2016'
      ? 'Avalanche problems were collected in 2026 only. Set Year to 2026 or Both to see this chart.'
      : 'No 2026 respondents match the current filters.'); return; }
  const N=DATA.scenarios.length, xs=[],ys=[],sz=[],co=[],tx=[],lbl=[];
  for(let si=0; si<N; si++){
    const sc=DATA.scenarios[si];
    const total=recs.filter(r=>r['P'+sc]!=null).length;
    for(let ci=0; ci<PROBCATS.length; ci++){
      const cnt=recs.filter(r=>r['P'+sc]===PROBCATS[ci]).length;
      if(!cnt) continue;
      const frac=total? cnt/total : 0;
      xs.push(ci); ys.push(N-1-si);
      sz.push(Math.sqrt(frac)*64+8);
      co.push(PROBCOLOR[PROBCATS[ci]]);
      lbl.push(frac>=0.12? String(cnt) : '');
      tx.push('S'+sc+' • '+PROBCATS[ci]+'<br>'+cnt+' of '+total+' ('+Math.round(frac*100)+'%)');
    }
  }
  Plotly.newPlot('probbubble',[{x:xs,y:ys,mode:'markers+text',type:'scatter',
    marker:{size:sz,color:co,line:{color:'#fff',width:1},sizemode:'diameter'},
    text:lbl,textfont:{color:'#fff',size:11},textposition:'middle center',
    customdata:tx,hovertemplate:'%{customdata}<extra></extra>'}],
   {margin:{t:10,r:10,b:96,l:36},
    xaxis:{tickvals:[0,1,2,3,4],ticktext:PROBCATS,range:[-0.7,4.7],tickangle:-18,zeroline:false,showgrid:true,gridcolor:'#eef0f2'},
    yaxis:{tickvals:DATA.scenarios.map((s,i)=>N-1-i),ticktext:DATA.scenarios.map(s=>'S'+s),range:[-0.7,N-0.3],zeroline:false,showgrid:false},
    font:{size:12},plot_bgcolor:'#fff'},
   {displayModeBar:false,responsive:true});
}

function rerender(){'''
assert 'function rerender(){' in raw
raw=raw.replace('function rerender(){', JS, 1)

hook='  renderProblems(recs);\n  refreshNote(recs);'
assert hook in raw
raw=raw.replace(hook, '  renderProblems(recs);\n  renderProblemBubble(recs);\n  refreshNote(recs);', 1)

open('index.html','w').write(raw)
print('added problem bubble panel OK')
