(function () {
  'use strict';

  var STARTERS = [
    'Rooms & prices',
    'What is the check-in time?',
    'Cancellation policy',
    'Check my booking'
  ];
  var WELCOME = 'Hi! Welcome to Binghomestay Support. How can I help you today?';

  var messagesEl = document.getElementById('messages');
  var chipsEl = document.getElementById('chips');
  var form = document.getElementById('form');
  var input = document.getElementById('input');
  var sendBtn = document.getElementById('send');
  var banner = document.getElementById('humanBanner');
  var statusDot = document.getElementById('statusDot');
  var statusText = document.getElementById('statusText');

  var history = [];
  var busy = false;

  function scrollDown() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addMessage(role, text) {
    var div = document.createElement('div');
    div.className = 'msg ' + role;
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollDown();
    return div;
  }

  function addBadge() {
    var b = document.createElement('div');
    b.className = 'badge';
    b.textContent = 'Human agent requested';
    messagesEl.appendChild(b);
  }

  function showTyping() {
    var t = document.createElement('div');
    t.className = 'typing';
    t.setAttribute('role', 'status');
    t.setAttribute('aria-label', 'Assistant is typing');
    for (var i = 0; i < 3; i++) t.appendChild(document.createElement('span'));
    messagesEl.appendChild(t);
    scrollDown();
    return t;
  }

  function setChips(list) {
    chipsEl.textContent = '';
    (list || []).forEach(function (label) {
      if (typeof label !== 'string' || !label.trim()) return;
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.textContent = label;
      b.addEventListener('click', function () { send(label); });
      chipsEl.appendChild(b);
    });
  }

  function setBusy(v) {
    busy = v;
    sendBtn.disabled = v;
  }

  async function send(text) {
    text = (text || '').trim();
    if (!text || busy) return;
    setBusy(true);
    setChips([]);
    addMessage('user', text);
    var prior = history.slice();
    history.push({ role: 'user', content: text });
    input.value = '';
    autosize();
    var typing = showTyping();

    try {
      var res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: prior })
      });
      if (!res.ok) {
        var err = new Error('HTTP ' + res.status);
        err.serverReached = true;
        err.status = res.status;
        try { err.detail = (await res.json()).detail; } catch (_) {}
        throw err;
      }
      var data = await res.json();
      typing.remove();
      var reply = String(data.reply == null ? '' : data.reply);
      addMessage('assistant', reply);
      history.push({ role: 'assistant', content: reply });
      if (data.needs_human) {
        banner.hidden = false;
        addBadge();
      }
      setChips(Array.isArray(data.suggested_actions) ? data.suggested_actions : []);
      setStatus(true);
    } catch (e) {
      typing.remove();
      history.pop(); // drop the unanswered user turn so a retry stays consistent
      if (e && e.serverReached) {
        var d = typeof e.detail === 'string' && /credit balance/i.test(e.detail)
          ? 'The AI provider account has no credits left.'
          : 'The support agent hit an error (HTTP ' + e.status + '). Please try again shortly.';
        addMessage('error', d);
        console.error('Chat error:', e.detail);
        setStatus(true);
      } else {
        addMessage('error', 'Sorry, I could not reach the support server. Please check your connection and try again.');
        setStatus(false);
      }
    } finally {
      setBusy(false);
      scrollDown();
      input.focus();
    }
  }

  function setStatus(ok) {
    statusDot.className = 'dot ' + (ok ? 'online' : 'offline');
    statusText.textContent = ok ? 'Online' : 'Offline';
  }

  async function checkHealth() {
    try {
      var r = await fetch('/api/health');
      var d = await r.json();
      setStatus(r.ok && d && d.status === 'ok');
    } catch (e) {
      setStatus(false);
    }
  }

  function reset() {
    history = [];
    messagesEl.textContent = '';
    banner.hidden = true;
    addMessage('assistant', WELCOME);
    setChips(STARTERS);
    input.focus();
  }

  function autosize() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 140) + 'px';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    send(input.value);
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      send(input.value);
    }
  });
  input.addEventListener('input', autosize);
  document.getElementById('newChat').addEventListener('click', reset);

  reset();
  checkHealth();
  setInterval(checkHealth, 30000);
})();
