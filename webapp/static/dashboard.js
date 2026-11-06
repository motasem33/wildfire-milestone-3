const fmt = new Intl.NumberFormat('en-US');
Chart.defaults.font.family = "'DM Sans', 'Manrope', Arial, sans-serif";
Chart.defaults.color = '#718079';
Chart.defaults.borderColor = '#e9ede7';
Chart.defaults.plugins.legend.labels.usePointStyle = true;

const charts = {};
const palette = {forest:'#527866', forestDark:'#365c4a', ember:'#c66b4e', gold:'#c69c59', muted:'#aeb9b2', grid:'#e9ede7'};

function chartOptions(extra={}) {
  return {
    responsive:true,
    maintainAspectRatio:false,
    animation:{duration:420},
    interaction:{mode:'index',intersect:false},
    plugins:{legend:{labels:{boxWidth:8,boxHeight:8,padding:15,font:{size:10}}},tooltip:{backgroundColor:'#192827',titleFont:{size:11},bodyFont:{size:10},padding:10,cornerRadius:8}},
    scales:{
      x:{grid:{display:false},ticks:{font:{size:9},maxRotation:0,autoSkip:true}},
      y:{beginAtZero:true,grid:{color:palette.grid},ticks:{font:{size:9},precision:0}}
    },
    ...extra
  };
}

function setChart(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), config);
}

const cvErrorBars = {
  id:'cvErrorBars',
  afterDatasetsDraw(chart) {
    if (chart.options.indexAxis !== 'y') return;
    const dataset=chart.data.datasets[0];
    const bars=chart.getDatasetMeta(0).data;
    if (!dataset.errorBars) return;
    const scale=chart.scales.x;
    const ctx=chart.ctx;
    ctx.save();
    ctx.strokeStyle='#33433d';
    ctx.lineWidth=1.4;
    bars.forEach((bar,index)=>{
      const mean=dataset.data[index];
      const spread=dataset.errorBars[index];
      const left=scale.getPixelForValue(Math.max(0,mean-spread));
      const right=scale.getPixelForValue(mean+spread);
      const y=bar.y;
      ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.moveTo(left,y-4);ctx.lineTo(left,y+4);ctx.moveTo(right,y-4);ctx.lineTo(right,y+4);ctx.stroke();
    });
    ctx.restore();
  }
};

function showToast(message) {
  const node = document.getElementById('toast');
  node.textContent = message;
  node.classList.add('show');
  window.setTimeout(() => node.classList.remove('show'), 2600);
}

function getFilters() {
  return {
    from_year: document.getElementById('fromYear').value,
    to_year: document.getElementById('toYear').value,
    season: document.getElementById('season').value
  };
}

function setDownloadLink() {
  const params = new URLSearchParams(getFilters());
  document.getElementById('downloadLink').href = `/download/filtered.csv?${params}`;
}

async function fetchJson(url) {
  const response = await fetch(url, {headers:{'Accept':'application/json'}});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Unable to load project data.');
  return body;
}

function renderPreview(rows) {
  const tbody = document.getElementById('dataRows');
  document.getElementById('tableCount').textContent = `${rows.length} rows`;
  tbody.replaceChildren();
  if (!rows.length) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 7; td.className = 'empty-state'; td.textContent = 'No records match the selected filters.';
    tr.append(td); tbody.append(tr); return;
  }
  rows.forEach(row => {
    const tr = document.createElement('tr');
    const values = [row.DATE, row.SEASON,
      Number.isFinite(Number(row.MAX_TEMP)) ? Number(row.MAX_TEMP).toFixed(0) : '—',
      Number.isFinite(Number(row.MIN_TEMP)) ? Number(row.MIN_TEMP).toFixed(0) : '—',
      Number.isFinite(Number(row.AVG_WIND_SPEED)) ? Number(row.AVG_WIND_SPEED).toFixed(2) : '—',
      Number.isFinite(Number(row.PRECIPITATION)) ? Number(row.PRECIPITATION).toFixed(2) : '—'];
    values.forEach(value => {const td=document.createElement('td');td.textContent=value;tr.append(td);});
    const status=document.createElement('td');
    const badge=document.createElement('span');
    badge.className=row.FIRE_START_DAY==='Fire start'?'badge-fire':'badge-clear';
    badge.textContent=row.FIRE_START_DAY==='Fire start'?'Recorded fire start':'No recorded start';
    status.append(badge);tr.append(status);
  });
}

async function loadOverview() {
  setDownloadLink();
  const params = new URLSearchParams(getFilters());
  try {
    const data = await fetchJson(`/api/overview?${params}`);
    document.getElementById('daysKpi').textContent = fmt.format(data.kpis.days);
    document.getElementById('eventsKpi').textContent = fmt.format(data.kpis.events);
    document.getElementById('rateKpi').textContent = `${data.kpis.rate.toFixed(1)}%`;
    document.getElementById('rangeKpi').textContent = `${data.kpis.from} — ${data.kpis.to}`;
    renderPreview(data.preview);
    const years=data.yearly.map(x=>x.year);
    setChart('yearChart',{type:'bar',data:{labels:years,datasets:[
      {type:'bar',label:'Recorded fire-start days',data:data.yearly.map(x=>x.events),backgroundColor:'rgba(82,120,102,.72)',borderRadius:3,maxBarThickness:13,yAxisID:'y'},
      {type:'line',label:'Positive-label rate %',data:data.yearly.map(x=>x.rate),borderColor:palette.ember,backgroundColor:palette.ember,pointRadius:0,pointHoverRadius:3,borderWidth:2,tension:.25,yAxisID:'y1'}
    ]},options:chartOptions({scales:{x:{grid:{display:false},ticks:{font:{size:9},maxRotation:0,autoSkip:true,maxTicksLimit:15}},y:{beginAtZero:true,position:'left',title:{display:true,text:'Recorded days',font:{size:9}},grid:{color:palette.grid},ticks:{font:{size:9},precision:0}},y1:{beginAtZero:true,position:'right',title:{display:true,text:'Rate %',font:{size:9}},grid:{drawOnChartArea:false},ticks:{font:{size:9},callback:v=>`${v}%`}}}})});
    setChart('seasonChart',{type:'bar',data:{labels:data.seasons.map(x=>x.label),datasets:[{label:'Positive-label rate %',data:data.seasons.map(x=>x.rate),backgroundColor:['#758f7f','#bdc9bb','#c66b4e','#bd9d69'],borderRadius:6,maxBarThickness:45}]},options:chartOptions({plugins:{legend:{display:false},tooltip:chartOptions().plugins.tooltip},scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{beginAtZero:true,grid:{color:palette.grid},ticks:{font:{size:9},callback:v=>`${v}%`}}}})});
    setChart('tempChart',{type:'bar',data:{labels:data.temperature.map(x=>x.label),datasets:[{label:'Positive-label rate %',data:data.temperature.map(x=>x.rate),backgroundColor:['#bcc9c1','#8ba194','#748c7d','#c66b4e'],borderRadius:6,maxBarThickness:48}]},options:chartOptions({plugins:{legend:{display:false},tooltip:chartOptions().plugins.tooltip},scales:{x:{grid:{display:false},ticks:{font:{size:9}}},y:{beginAtZero:true,grid:{color:palette.grid},ticks:{font:{size:9},callback:v=>`${v}%`}}}})});
  } catch (error) {
    showToast(error.message);
  }
}

async function loadModels() {
  try {
    const data=await fetchJson('/api/models');
    document.getElementById('selectedModel').textContent=data.selected;
    const rows=[...data.rows].sort((a,b)=>a.cv_average_precision_mean-b.cv_average_precision_mean);
    document.getElementById('modelDetails').replaceChildren(...[...rows].reverse().map(row=>{
      const item=document.createElement('div');item.className='model-detail-row';
      const name=document.createElement('span');name.textContent=row.model;
      const score=document.createElement('strong');score.textContent=`${(row.cv_average_precision_mean*100).toFixed(1)}% ± ${(row.cv_average_precision_std*100).toFixed(1)}`;
      item.append(name,score);return item;
    }));
    setChart('modelChart',{type:'bar',plugins:[cvErrorBars],data:{labels:rows.map(r=>r.model),datasets:[{label:'Mean Average Precision',data:rows.map(r=>r.cv_average_precision_mean*100),backgroundColor:rows.map(r=>r.model===data.selected?palette.ember:'#80998b'),borderRadius:5,maxBarThickness:32,errorBars:rows.map(r=>r.cv_average_precision_std*100)}]},options:chartOptions({indexAxis:'y',plugins:{legend:{display:false},tooltip:{...chartOptions().plugins.tooltip,callbacks:{label:ctx=>` AP ${ctx.raw.toFixed(1)}% ± ${ctx.dataset.errorBars[ctx.dataIndex].toFixed(1)} pp`}}},scales:{x:{beginAtZero:true,max:85,grid:{color:palette.grid},ticks:{font:{size:9},callback:v=>`${v}%`}},y:{grid:{display:false},ticks:{font:{size:9}}}}})});
  } catch(error) {showToast(error.message);}
}

function renderThreshold(data) {
  document.getElementById('accuracyMetric').textContent=`${data.accuracy.toFixed(1)}%`;
  document.getElementById('recallMetric').textContent=`${data.recall.toFixed(1)}%`;
  document.getElementById('precisionMetric').textContent=`${data.precision.toFixed(1)}%`;
  document.getElementById('f1Metric').textContent=`${data.f1.toFixed(1)}%`;
  document.getElementById('matrixThreshold').textContent=Number(data.threshold).toFixed(2);
  document.getElementById('thresholdValue').textContent=Number(data.threshold).toFixed(2);
  document.getElementById('tnCell').textContent=fmt.format(data.matrix[0][0]);
  document.getElementById('fpCell').textContent=fmt.format(data.matrix[0][1]);
  document.getElementById('fnCell').textContent=fmt.format(data.matrix[1][0]);
  document.getElementById('tpCell').textContent=fmt.format(data.matrix[1][1]);
}

let thresholdTimer;
async function updateThreshold(value) {
  document.getElementById('thresholdValue').textContent=Number(value).toFixed(2);
  window.clearTimeout(thresholdTimer);
  thresholdTimer=window.setTimeout(async()=>{
    try {renderThreshold(await fetchJson(`/api/threshold?value=${encodeURIComponent(value)}`));}
    catch(error){showToast(error.message);}
  },80);
}

async function loadTestAndFeatures() {
  try {
    const data=await fetchJson('/api/test');
    const m=data.test_metrics;
    document.getElementById('aucMetric').textContent=Number(m.roc_auc*100).toFixed(1)+'%';
    document.getElementById('apMetric').textContent=Number(m.average_precision*100).toFixed(1)+'%';
    renderThreshold(data.threshold_view);
    const items=data.feature_importance;
    setChart('featureChart',{type:'bar',data:{labels:items.map(x=>x.feature).reverse(),datasets:[{label:'Decrease in Average Precision',data:items.map(x=>x.importance*100).reverse(),backgroundColor:items.map((_,i)=>i<3?'rgba(198,107,78,.82)':'rgba(82,120,102,.7)').reverse(),borderRadius:4,maxBarThickness:19}]},options:chartOptions({indexAxis:'y',plugins:{legend:{display:false},tooltip:{...chartOptions().plugins.tooltip,callbacks:{label:ctx=>` AP decrease: ${ctx.raw.toFixed(2)} percentage points`}}},scales:{x:{beginAtZero:true,grid:{color:palette.grid},ticks:{font:{size:9},callback:v=>`${v}%`}},y:{grid:{display:false},ticks:{font:{size:9}}}}})});
  } catch(error) {showToast(error.message);}
}

document.getElementById('applyFilters').addEventListener('click',()=>{
  const from=document.getElementById('fromYear');
  const to=document.getElementById('toYear');
  if(Number(from.value)>Number(to.value)){showToast('The start year must not exceed the end year.');return;}
  loadOverview();
});
document.getElementById('season').addEventListener('change',loadOverview);
document.getElementById('thresholdSlider').addEventListener('input',event=>updateThreshold(event.target.value));

const sectionLinks=[...document.querySelectorAll('.nav-link')];
const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
  if(entry.isIntersecting){sectionLinks.forEach(link=>link.classList.toggle('active',link.getAttribute('href')===`#${entry.target.id}`));}
}),{rootMargin:'-25% 0px -65% 0px'});
document.querySelectorAll('main section[id]').forEach(section=>observer.observe(section));

loadOverview();
loadModels();
loadTestAndFeatures();
