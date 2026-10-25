let roles = {};
const roleSelect = document.getElementById('role');
const questionsEl = document.getElementById('questions');
const messageEl = document.getElementById('message');

async function loadRoles(){
  const res = await fetch('/api/roles');
  roles = await res.json();
  roleSelect.innerHTML = Object.keys(roles).map(r=>`<option>${r}</option>`).join('');
  renderQuestions();
}

function renderQuestions(){
  const role = roles[roleSelect.value];
  if(!role) return;
  document.getElementById('roleDescription').textContent = role.description;
  questionsEl.innerHTML = role.questions.map((q,i)=>`
    <div class="question">
      <div class="question-head"><div><div class="competency">${q.competency.replaceAll('_',' ')}</div><h3>${i+1}. ${q.question}</h3></div><button type="button" class="voice" data-index="${i}">🎙 Voice</button></div>
      <textarea id="answer-${i}" placeholder="Use STAR: situation → task → action → result"></textarea>
    </div>`).join('');
  bindVoice();
}

function bindVoice(){
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  document.querySelectorAll('.voice').forEach(btn=>btn.onclick=()=>{
    if(!SpeechRecognition){ messageEl.textContent='Voice transcription is not supported in this browser.'; return; }
    const rec = new SpeechRecognition();
    rec.lang = 'en-NZ'; rec.interimResults = false; rec.continuous = false;
    btn.textContent='Listening…';
    rec.onresult = e => { document.getElementById(`answer-${btn.dataset.index}`).value += (document.getElementById(`answer-${btn.dataset.index}`).value?' ':'') + e.results[0][0].transcript; };
    rec.onerror = ()=> messageEl.textContent='Voice transcription could not start. You can type your answer instead.';
    rec.onend = ()=> btn.textContent='🎙 Voice';
    rec.start();
  });
}

function metric(label,value){ return `<div class="metric"><span class="muted">${label}</span><strong>${value}%</strong></div>`; }
function renderDashboard(data){
  const results = document.getElementById('results'); results.classList.remove('hidden');
  document.getElementById('scoreBadge').textContent = `${data.final_score}/100`;
  const avg = key => Math.round(data.evaluations.reduce((s,x)=>s+x[key],0)/data.evaluations.length);
  document.getElementById('dimensionCards').innerHTML = metric('Relevance',avg('relevance'))+metric('Evidence',avg('evidence'))+metric('Clarity',avg('clarity'))+metric('STAR',avg('star'))+metric('Semantic fit',avg('semantic'));
  document.getElementById('feedback').innerHTML = data.evaluations.map((x,i)=>`<div class="feedback-card"><strong>${i+1}. ${x.competency.replaceAll('_',' ')} — ${x.overall}/100</strong><ul>${x.feedback.map(f=>`<li>${f}</li>`).join('')}</ul></div>`).join('');
  renderHistory(data.history,data.competencies);
  results.scrollIntoView({behavior:'smooth'});
}
function renderHistory(history,competencies){
  document.getElementById('competencies').innerHTML = (competencies||[]).map(x=>`<div class="bar-row"><span>${x.competency.replaceAll('_',' ')}</span><div class="bar-track"><div class="bar-fill" style="width:${x.average_score}%"></div></div><strong>${x.average_score}</strong></div>`).join('') || '<p class="muted">Complete an interview to build competency trends.</p>';
  document.getElementById('history').innerHTML = (history||[]).map(x=>`<div class="history-row"><strong>${x.role}</strong><span class="muted">${x.created_at}</span><strong>${x.final_score}</strong></div>`).join('') || '<p class="muted">No completed sessions yet.</p>';
}

roleSelect.addEventListener('change',renderQuestions);
document.getElementById('interviewForm').addEventListener('submit',async e=>{
  e.preventDefault(); messageEl.textContent='Evaluating…'; messageEl.className='message';
  const role = roleSelect.value;
  const answers = roles[role].questions.map((_,i)=>document.getElementById(`answer-${i}`).value.trim());
  const res = await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({candidate:document.getElementById('candidate').value,role,answers})});
  const data = await res.json();
  if(!res.ok){ messageEl.textContent=data.error||'Unable to evaluate interview.'; return; }
  messageEl.textContent='Interview evaluated and saved.'; messageEl.className='message ok'; renderDashboard(data);
});
document.getElementById('historyBtn').addEventListener('click',async()=>{
  const name = encodeURIComponent(document.getElementById('candidate').value);
  const data = await (await fetch(`/api/history?candidate=${name}`)).json();
  document.getElementById('results').classList.remove('hidden'); renderHistory(data.history,data.competencies);
});
loadRoles();
