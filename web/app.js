(function(){
"use strict";
var D = window.OLPARK, M = D.surge_model, $ = function(s){return document.querySelector(s)};
var COLORS=["var(--chart-1)","var(--chart-2)","var(--chart-3)","var(--chart-4)","var(--chart-5)"];
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}

/* 탭 */
var tabs=document.querySelectorAll(".tabs button");
function show(name){
  tabs.forEach(function(b){b.setAttribute("aria-selected",String(b.dataset.tab===name))});
  document.querySelectorAll(".panel").forEach(function(p){p.hidden=(p.id!=="tab-"+name)});
  window.scrollTo(0,0);
}
tabs.forEach(function(b){b.addEventListener("click",function(){show(b.dataset.tab)})});

/* 규모별 데이터 */
var S25=D.surge2025;
var SCALES={
  small:{name:"중소 규모",T:M.t_clear,max:60,steps:[0,20,40],axis:M.profile_axis_min,
    series:Object.keys(M.profiles).map(function(k){return {label:k.slice(5),v:M.profiles[k],partial:false}}),
    src:"2024-07 공연일 5회 실측"},
  large:{name:"대규모",T:S25.t_clear,max:120,steps:[0,30,60],axis:S25.profile_axis_min,
    series:S25.days.map(function(d){return {label:d.date.slice(5)+(d.partial?" (일부)":""),v:d.profile,partial:d.partial}}),
    src:"2025-12 대규모 콘서트 2회 실측(관람객 2만 명대)"}
};
var scale="small";
function waitAt(key,off){return Math.max(0,Math.round(SCALES[scale].T[key]-off))}
function fmtRange(a,b){return a===b?a+"분":a+"~"+b+"분"}
var off=$("#offset");
function renderOut(){
  var C=SCALES[scale], s=+off.value;
  $("#offsetOut").textContent=s===0?"몰림 시작":s+"분 경과";
  var lo=waitAt("lo",s),md=waitAt("med",s),hi=waitAt("hi",s);
  $("#waitMed").textContent=md;
  $("#waitRange").textContent="범위 "+fmtRange(lo,hi)+" ("+C.src+"의 최소와 최대)";
  var cmp=C.steps.map(function(d){var t=Math.min(C.max,s+d);var m=waitAt("med",t);
    return '<div class="cmp'+(d===0?' now':'')+'"><span>'+(d===0?"지금 출발":"+"+d+"분 뒤")+'</span><b>'+m+"분"+'</b></div>'}).join("");
  $("#compare").innerHTML=cmp;
  var next=$("#nextStep");
  if(md>=10){
    var walk=Math.max(10,Math.min(60,Math.round(md/5)*5));
    next.innerHTML='<h2>기다리는 대신 걷기</h2><p>지금 줄에 서면 대기가 최대 약 '+md+'분일 수 있습니다(상한 추정). 차 안에서 기다리지 말고 약 '+walk+'분 산책 후 돌아오면, 그때는 출차 몰림이 많이 풀려 있을 것으로 보입니다.</p><button class="cta" id="goWalk">'+walk+'분 산책 코스 보기</button>';
    $("#goWalk").addEventListener("click",function(){var sel=$("#walkMin");sel.value=String(walk<=15?15:walk<=25?25:walk<=40?40:60);renderCourse();show("walk")});
  }else{
    next.innerHTML='<h2>지금 출발해도 좋아요</h2><p>이 시점에는 몰림이 거의 풀린 것으로 추정됩니다. 그래도 주차장 출구 앞은 보행자와 차량이 섞이니 주의하세요.</p>';
  }
  drawChart(s);
}
off.addEventListener("input",renderOut);
function setScale(k){
  scale=k; var C=SCALES[k];
  off.max=C.max; if(+off.value>C.max)off.value=C.max;
  document.querySelectorAll(".seg button").forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.scale===k))});
  renderOut();
}
document.querySelectorAll(".seg button").forEach(function(b){b.addEventListener("click",function(){setScale(b.dataset.scale)})});

/* 차트 */
function drawChart(sel){
  var C=SCALES[scale], ax=C.axis, ser=C.series;
  var W=360,H=200,pl=30,pr=10,pt=10,pb=30;
  var maxY=0;ser.forEach(function(x){x.v.forEach(function(v){if(v>maxY)maxY=v})});maxY=Math.ceil(maxY/20)*20;
  function X(m){return pl+(m-ax[0])/(ax[ax.length-1]-ax[0])*(W-pl-pr)}
  function Y(v){return pt+(1-v/maxY)*(H-pt-pb)}
  var g="";
  for(var y=0;y<=maxY;y+=maxY/4){g+='<line x1="'+pl+'" x2="'+(W-pr)+'" y1="'+Y(y)+'" y2="'+Y(y)+'" stroke="currentColor" opacity=".12"/><text x="'+(pl-4)+'" y="'+(Y(y)+3)+'" font-size="9" text-anchor="end" fill="currentColor" opacity=".6">'+Math.round(y)+'</text>'}
  var tickEnd=ax[ax.length-1], ticks=[];for(var m=-30;m<=tickEnd;m+=30)ticks.push(m);
  ticks.forEach(function(m){g+='<text x="'+X(m)+'" y="'+(H-pb+12)+'" font-size="9" text-anchor="middle" fill="currentColor" opacity=".6">'+m+'</text>'});
  var full=ser.filter(function(x){return !x.partial});
  var med=ax.map(function(_,i){var a=full.map(function(x){return x.v[i]}).sort(function(p,q){return p-q});return a[Math.floor(a.length/2)]});
  var lines="";
  ser.forEach(function(x,ki){var d=x.v.map(function(v,i){return (i?"L":"M")+X(ax[i]).toFixed(1)+" "+Y(v).toFixed(1)}).join("");
    lines+='<path d="'+d+'" fill="none" stroke="'+COLORS[ki%5]+'" stroke-width="1.4" opacity=".6"'+(x.partial?' stroke-dasharray="4 3"':'')+'/>'});
  var dm=med.map(function(v,i){return (i?"L":"M")+X(ax[i]).toFixed(1)+" "+Y(v).toFixed(1)}).join("");
  var mark='<line x1="'+X(sel)+'" x2="'+X(sel)+'" y1="'+pt+'" y2="'+(H-pb)+'" stroke="var(--danger)" stroke-width="1.5" stroke-dasharray="3 3"/>';
  $("#chart").innerHTML='<svg viewBox="0 0 '+W+' '+H+'" role="img">'+g+lines+'<path d="'+dm+'" fill="none" stroke="currentColor" stroke-width="2.4"/>'+mark+'<text x="'+(pl)+'" y="8" font-size="9" fill="currentColor" opacity=".6">대/5분</text><text x="'+(W/2)+'" y="'+(H-0)+'" font-size="9" text-anchor="middle" fill="currentColor" opacity=".6">몰림 시작 후 경과(분)</text></svg>';
  $("#legend").innerHTML=ser.map(function(x,ki){return '<span><i style="background:'+COLORS[ki%5]+'"></i>'+x.label+'</span>'}).join("")+'<span><b>━</b> 중앙값'+(ser.length!==full.length?' (일부 제외)':'')+'</span><span class="mark-key">┆ 선택 시점</span>';
}
/* 공연 시작 시각 -> 몰림 시작 추정 (공연정보 API의 공연 시간 + 게이트 파일의 종료 후 간격) */
function pad(n){return String(n).padStart(2,"0")}
function renderOnset(){
  var v=$("#showStart").value, el=$("#onsetNote");
  if(!v){el.textContent="공연 시작 시각을 넣으면 출차 몰림이 시작될 시각을 추정해 드립니다.";return}
  var p=v.split(":"), m=(+p[0])*60+(+p[1]), dur=+$("#showDur").value, gap=D.gap.gap_min.lo;
  var end=m+dur, on=end+gap;
  function f(x){x=((x%1440)+1440)%1440;return pad(Math.floor(x/60))+":"+pad(x%60)}
  el.innerHTML="종료 약 <b>"+f(end)+"</b>, 출차 몰림은 약 <b>"+f(on)+"</b>부터(종료 후 약 "+gap+"분, 2025-12 대규모 공연 "+D.gap.gap_min.n+"회 모두 같았음). 이 시각을 0분으로 아래 슬라이더를 보세요. 추정입니다.";
}
$("#showStart").addEventListener("input",renderOnset);$("#showDur").addEventListener("change",renderOnset);
/* 출구 이용 비중 */
function renderGates(){
  var days=S25.days.filter(function(d){return !d.partial});
  var keys=["남2문","동2문","북2문"], rest=0, acc={};
  days.forEach(function(d){keys.forEach(function(k){acc[k]=(acc[k]||0)+d.gate_share[k]});
    var o=0;Object.keys(d.gate_share).forEach(function(k){if(keys.indexOf(k)<0)o+=d.gate_share[k]});rest+=o});
  var n=days.length, rows=keys.map(function(k){return [k+" (2차선)",acc[k]/n]}).concat([["기타 (서2·남4·남3·서1문, 각 1차선)",rest/n]]);
  $("#gates").innerHTML=rows.map(function(r){return '<div class="bar"><b>'+esc(r[0].indexOf('기타')===0?'기타':r[0].split(' ')[0])+'</b><div class="track"><i class="s-ok" style="width:'+r[1]+'%"></i></div><span>'+r[1].toFixed(0)+'%</span></div>'}).join("")+
    '<p class="muted">2025-12 대규모 공연 서지 구간('+n+'회)의 출구별 출차 비중. 남2·동2·북2문 출구가 약 '+(100-rest/n).toFixed(0)+'%를 처리하고, 서2·남4·남3·서1문은 합쳐 '+(rest/n).toFixed(0)+'% 안팎입니다. 주차한 위치에서 갈 수 있는 다른 출구가 있는지 확인해 볼 만합니다(출구 간 이동 거리 데이터는 없음).</p>';
}

/* 산책 코스 */
var POIS=[
 {n:"나홀로나무",t:10,src:"data",rule:"always",m:"잔디시설정보: 연중 상시개방"},
 {n:"피크닉장",t:8,src:"data",rule:"always",m:"잔디시설정보: 연중 상시개방"},
 {n:"가족놀이동산",t:8,src:"data",rule:"always",m:"잔디시설정보: 연중 상시개방"},
 {n:"88마당",t:10,src:"data",rule:"lawn",m:"잔디시설정보: 06-01~10-31 개방"},
 {n:"지구촌공원",t:10,src:"data",rule:"lawn",m:"잔디시설정보: 06-01~10-31 개방"},
 {n:"전시마당",t:8,src:"data",rule:"lawn",m:"잔디시설정보: 06-01~10-31 개방"},
 {n:"장미광장 한 바퀴",t:10,src:"gen",rule:"always",m:"수록 장미 품종·개화 정보는 오픈API(15056986) 연동 후 반영"},
 {n:"몽촌호수 둘레 산책",t:20,src:"gen",rule:"always",m:"일반 안내 기반, 개방 시간은 현장 확인"}
];
function lawnOpen(dstr){var d=new Date(dstr+"T00:00:00");var md=(d.getMonth()+1)*100+d.getDate();return md>=601&&md<=1031}
function renderCourse(){
  var mins=+$("#walkMin").value, ds=$("#walkDate").value, night=$("#walkNight").checked;
  var lawn=lawnOpen(ds), budget=Math.max(5,mins-8); // 이동·복귀 여유 8분(추정)
  var list=POIS.filter(function(p){return p.rule==="always"||lawn});
  var order=["장미광장 한 바퀴","나홀로나무","피크닉장","가족놀이동산","88마당","지구촌공원","전시마당","몽촌호수 둘레 산책"];
  list.sort(function(a,b){return order.indexOf(a.n)-order.indexOf(b.n)});
  if(mins<=15) list=list.filter(function(p){return p.t<=15});
  var pick=[],sum=0;list.forEach(function(p){if(sum+p.t<=budget){pick.push(p);sum+=p.t}});
  var h="";
  if(!pick.length){h='<p>이 시간으로는 코스를 만들기 어렵습니다. 주차장 근처에서 잠깐 걷는 정도를 권합니다.</p>'}
  else{
    h=pick.map(function(p,i){return '<div class="stop"><div class="num">'+i+1+'</div><div><b>'+esc(p.n)+'<span class="pill'+(p.src==="data"?"":" g")+'">'+(p.src==="data"?"공공데이터":"일반 안내")+'</span></b><div class="m">약 '+p.t+'분. '+esc(p.m)+'</div></div></div>'}).join("");
    h+='<p class="muted note-gap">걷기 약 '+sum+'분 + 이동·복귀 여유 약 8분 = 약 '+(sum+8)+'분 (모두 추정). 출차 몰림이 풀린 뒤 차로 돌아가세요.</p>';
  }
  $("#course").innerHTML=h;
  var notes=[];
  notes.push(lawn?"선택한 날짜는 잔디시설 개방기간(06-01~10-31) 안입니다.":"선택한 날짜는 잔디 출입금지기간(11-01~익년05-31)이라 88마당·지구촌공원·전시마당은 코스에서 뺐습니다. 나홀로나무·피크닉장·가족놀이동산은 데이터상 연중 상시개방입니다.");
  if(night)notes.push("야간 개방·조명 정보는 제공 데이터에 없습니다. 어두운 시간에는 밝은 길 위주로, 안내 직원의 지시를 따르세요.");
  notes.push("코스 소요시간은 보행 속도를 가정한 대략값(추정)입니다. 지도 좌표·거리는 데이터에 없어 정밀 경로는 제공하지 않습니다.");
  $("#seasonNote").innerHTML="<b>참고</b><br>"+notes.map(esc).join("<br>");
}
var today=new Date();var iso=today.getFullYear()+"-"+String(today.getMonth()+1).padStart(2,"0")+"-"+String(today.getDate()).padStart(2,"0");
$("#walkDate").value=iso;
["#walkMin","#walkDate","#walkNight"].forEach(function(s){$(s).addEventListener("change",renderCourse)});

/* 입차 전 */
function renderIn(){
  var mo=D.monthly.monthly_avg_op, tp=M.t_clear;
  $("#inTips").innerHTML=[
   "중소 규모 공연일(2024-07, "+M.surge_days.length+"회): 출차 몰림 코어 35~50분, 초과 출차 약 "+Math.min.apply(null,M.surge_days.map(function(d){return d.excess}))+"~"+Math.max.apply(null,M.surge_days.map(function(d){return d.excess}))+"대, 90%가 빠지기까지 "+tp.lo+"~"+tp.hi+"분.",
   "대규모 콘서트(2025-12, 관람객 약 2만 명대 "+S25.days.filter(function(d){return !d.partial}).length+"회): 몰림 코어 "+S25.days.filter(function(d){return !d.partial}).map(function(d){return d.dur}).join("~")+"분, 초과 출차 약 "+S25.days.filter(function(d){return !d.partial}).map(function(d){return d.excess.toLocaleString("ko-KR")}).join("~")+"대, 5분 최대 "+S25.days.map(function(d){return d.peak5}).join("·")+"대, 90%가 빠지기까지 "+S25.t_clear.lo+"~"+S25.t_clear.hi+"분.",
   "대규모 공연일에는 주차장이 약 3,000대 이상 찹니다(연계 데이터의 시간별 주차대수 최대 "+Math.max.apply(null,S25.days.map(function(d){return d.occupancy_max||0})).toLocaleString("ko-KR")+"대). 공연 종료 전에 출차 계획을 세워 두면 좋습니다.",
   "오늘 공연 종료 시각은 공연정보 연계(3037877) 후 안내할 예정입니다. 현재는 공연장 안내를 확인하세요.",
   "올림픽공원 월평균 주차 대수(2023~2025): 가장 붐비는 달 "+topMonth(mo)+"월, 가장 한산한 달 "+lowMonth(mo)+"월."
  ].map(function(t){return "<li>"+t+"</li>"}).join("");
  $("#lotCaveat").textContent=D.lots.caveat;
  var z=D.lots.zones;
  $("#lots").innerHTML=z.map(function(r){var t=r.records;return '<div class="bar"><b>'+esc(r.zone)+'</b><div class="track" title="만차 '+r.full+', 혼잡 '+r.busy+', 원활 '+r.ok+'"><i class="s-full" style="width:'+(r.full/t*100)+'%"></i><i class="s-busy" style="width:'+(r.busy/t*100)+'%"></i><i class="s-ok" style="width:'+(r.ok/t*100)+'%"></i></div><span>'+Math.round(r.full/t*100)+'%</span></div>'}).join("")+'<div class="legend"><span><i class="s-full"></i>만차</span><span><i class="s-busy"></i>혼잡</span><span><i class="s-ok"></i>원활</span><span>(기록 중 비중)</span></div>';
}
function topMonth(m){var b=1;Object.keys(m).forEach(function(k){if(m[k]>m[b])b=+k});return b}
function lowMonth(m){var b=1;Object.keys(m).forEach(function(k){if(m[k]<m[b])b=+k});return b}

/* 근거 */
function renderWhy(){
  var S=M.surge_days;
  var rows=S.map(function(d){return "<tr><td>"+d.date+"</td><td>"+d.peak5+"</td><td>"+d.cap_per_min+"</td><td>"+d.excess+"</td></tr>"}).join("");
  var rows25=S25.days.map(function(d){return "<tr><td>"+d.date+(d.partial?" (일부)":"")+"</td><td>"+d.peak5+"</td><td>"+d.peak_per_min+"</td><td>"+d.excess.toLocaleString("ko-KR")+"</td><td>"+d.t90+"</td><td>"+d.audience.toLocaleString("ko-KR")+"</td></tr>"}).join("");
  var holdQ=M.holdout_queue_mae_min, holdE=M.holdout_empirical_mae_min;
  $("#method").innerHTML=
   '<p class="muted"><b>중소 규모(2024-07)</b>: 입출차 원자료 215,528건에서 5분 단위 출차 대수를 만들고, 저녁 시간대 요일유형 기준선(평소 중앙값)보다 크게 늘어난 날을 공연 서지일로 검출했습니다('+M.n_surge_days+'/'+M.n_days_total+'일). 이 파일에는 게이트 정보가 없습니다.</p>'+
   '<table class="m"><tr><th>날짜</th><th>5분 최대(대)</th><th>처리율(대/분)</th><th>초과 출차(대)</th></tr>'+rows+'</table>'+
   '<p class="note-gap muted"><b>대규모(2025-12)</b>: 문화공공데이터광장의 2025 게이트별 입출차 파일(차량별 출구·차선, 10만 건)과 시간별 연계 데이터(공연명·관람객수)를 사용했습니다. 12월 1~4일(비공연일) 같은 시각 중앙값을 기준선으로 뺀 초과 출차량입니다. 12-07은 16:08 이후 입차분이 파일에 없어 일부만 반영됩니다. 시간별 연계 데이터는 12-05~07 구간만 썼고 게이트 파일과 상관 0.94로 교차 확인했습니다(다른 구간은 보간 가능성, 품질 제안 Q11).</p>'+
   '<table class="m"><tr><th>날짜</th><th>5분 최대(대)</th><th>대/분</th><th>초과 출차(대)</th><th>90% 해소(분)</th><th>관람객(명)</th></tr>'+rows25+'</table>'+
   '<p class="note-gap"><b>대기시간 추정</b>: 몰림 시작 후 s분에 줄에 서면 큐가 빌 때까지 남은 시간을 대기의 <u>상한</u>으로 봅니다(선입선출, 한꺼번에 도착 가정, 실제로는 도착이 분산되어 이보다 짧음). 큐가 비는 시점은 실측의 초과 출차 90% 도달 시간입니다: 중소 규모 '+M.t_clear.lo+'~'+M.t_clear.hi+'분(중앙 '+M.t_clear.med+'), 대규모 '+S25.t_clear.lo+'~'+S25.t_clear.hi+'분(표본 '+S25.t_clear.n+'회).</p>'+
   '<p><b>검증</b>(하루 제외 교차검증, 중소 규모 5일): 용량 기반 큐 모델은 90% 도달 시점 평균 오차 '+holdQ+'분으로 부정확했고, 단순 경험 평균 예측은 '+holdE+'분이라 후자를 채택했습니다. 대규모는 표본이 2회뿐이라 검증할 수 없습니다. <u>정합성 점검 수준이며 강한 검증이 아닙니다.</u></p>'+
   '<p class="note-gap muted"><b>공연 종료와 몰림 시작의 간격</b>: 공연정보 API(3037877)에는 2025-12 공연이 없지만, 같은 아티스트(god)의 과거 KSPO DOME 콘서트 '+D.gap.god_records.length+'건이 모두 150분이고, 가장 최근 2023·2024 시즌은 둘 다 금 20:00, 토 18:00, 일 17:00이어서 12-05(금)와 12-06(토)의 시작을 20:00과 18:00으로 보았습니다(입차 피크가 시작 약 75분 전으로 일치해 보강). 게이트 파일에서 초과 출차가 처음 연속 상승한 시각은 두 날 모두 종료 후 '+D.gap.days.map(function(x){return x.gap_min}).join("분, ")+'분이었습니다. 표본은 2회이고 시작 시각은 추정입니다. KSPO DOME 공연 시간 기록 '+D.perf_api.by_venue["KSPO DOME(체조경기장)"].n+'건의 중앙값은 '+D.perf_api.by_venue["KSPO DOME(체조경기장)"].median+'분입니다.</p>'+
   '<p class="muted"><b>한계</b>: 대기열 자체는 어느 파일에도 기록되어 있지 않아 정산 통과 시각의 분포로 간접 추정합니다. 차선별 1분 최대는 8~12대로 물리적 한계에 가깝지만 모든 차선이 계속 포화된 것은 아닙니다. 공연 시작 시각은 공연장 안내를 확인해 입력해야 합니다(공연정보 API에 2025-12 공연이 없음).</p>';
  var Q=D.quality;$("#qCount").textContent="("+Q.length+"건)";
  $("#quality").innerHTML=Q.map(function(q){return '<div class="q"><h3>'+esc(q.id)+". "+esc(q.dataset)+'<span class="sev">'+esc(q.severity)+'</span></h3><div>'+esc(q.finding)+'</div><div class="sg">제안: '+esc(q.suggestion)+'</div></div>'}).join("");
}

/* 실시간 주차현황 (15168686: 기관 공개 API, 출력 parking_sum). 실패 시 숨김 처리 */
function initLive(){
  var ep=(window.OLPARK_CONFIG||{}).liveEndpoint; if(!ep)return;
  fetch(ep,{cache:"no-store"}).then(function(r){return r.json()}).then(function(j){
    var n=Array.isArray(j)?j[0]&&j[0].parking_sum:j&&j.parking_sum;
    if(typeof n!=="number")throw new Error("bad");
    var hm=new Date().toTimeString().slice(0,5);
    $("#liveCard").hidden=false;$("#live").hidden=false;$("#liveText").textContent="실시간 "+n.toLocaleString("ko-KR")+"대";
    $("#liveBody").innerHTML='<div class="big big-sm">'+n.toLocaleString("ko-KR")+'<small>대 주차 중</small></div><p class="muted">동2문·남2문·북2문 주차구역 합계(공공데이터 15168686 \'parking_sum\'), 조회 '+hm+'. 전체 수용 대수는 데이터에 없어 혼잡 정도는 판단하지 않습니다.</p>';
  }).catch(function(){$("#liveCard").hidden=true;});
}
setScale("small");renderGates();renderCourse();renderIn();renderWhy();initLive();
})();
