// 1. FIX GEMINI ENDPOINT
function executeDeepGemini(prompt, cb) {
  var key = getSetting('gemini');
  if(!key) { cb({error: 'No Key'}); return; }
  
  // Changed from v1beta to v1
  var url = 'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=' + key;
  
  fetch(url, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
  })
  .then(res => res.json())
  .then(data => {
     if(data.error) cb({error: data.error.message});
     else cb({text: data.candidates[0].content.parts[0].text.trim()});
  })
  .catch(err => cb({error: 'Connection Timed Out'}));
}

// 2. FIX CALENDAR FETCH (Direct from your backend, NO PROXY)
async function fetchCalendarData() {
  showBar('cal-bar','loading','Fetching upcoming dates...');
  try {
      // Connects directly to your Render backend - No firewall issues
      const res = await fetch('https://fno-edge.onrender.com/api/calendar');
      const json = await res.json();
      CALENDAR = json.data.map(item => ({
          sym: (item.Security_Name || item.scrip_name || '').split(' ')[0],
          purpose: item.Purpose || item.HEADLINE || '',
          dStr: item.ExDate || item.ex_date || 'N/A',
          date: new Date(item.ExDate || item.ex_date || Date.now())
      }));
      renderCalendar();
      document.getElementById('cal-bar').style.display = 'none';
  } catch(e) { 
      showBar('cal-bar', 'err', 'Backend Connection Failed'); 
  }
}