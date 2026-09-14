/**
 * TaskPulse: Dynamic Task Engine & Local AI Dashboard Client
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- State ---
  let activeTab = 'intake';
  let speechRecognizer = null;
  let isListening = false;
  let reviewState = {};

  // --- Elements ---
  const navTabs = document.querySelectorAll('.nav-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  const btnMic = document.getElementById('btnMic');
  const intakeText = document.getElementById('intakeText');
  const voiceStatusMsg = document.getElementById('voiceStatusMsg');
  const btnDecompose = document.getElementById('btnDecompose');
  const decomposeSpinner = document.getElementById('decomposeSpinner');
  const planPreviewContainer = document.getElementById('planPreviewContainer');
  const timelineContainer = document.getElementById('timelineContainer');
  const btnRefreshSchedule = document.getElementById('btnRefreshSchedule');
  const btnSyncCalendar = document.getElementById('btnSyncCalendar');
  const reviewContainer = document.getElementById('reviewContainer');
  const btnSaveReview = document.getElementById('btnSaveReview');
  const quickIdeaInput = document.getElementById('quickIdeaInput');
  const btnSaveIdea = document.getElementById('btnSaveIdea');
  const ideasGrid = document.getElementById('ideasGrid');
  const btnRefreshTelemetry = document.getElementById('btnRefreshTelemetry');
  const toastContainer = document.getElementById('toastContainer');
  const dbStatusText = document.getElementById('dbStatusText');
  const calStatusText = document.getElementById('calStatusText');
  const calDot = document.getElementById('calDot');

  // --- Toast Notifications ---
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // --- Tab Navigation ---
  navTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.getAttribute('data-tab');
      switchTab(tabName);
    });
  });

  function switchTab(tabName) {
    activeTab = tabName;
    navTabs.forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === tabName));
    tabPanels.forEach(p => p.classList.toggle('active', p.id === `tab-${tabName}`));

    if (tabName === 'schedule') loadSchedule();
    if (tabName === 'review') loadReview();
    if (tabName === 'ideas') loadIdeas();
    if (tabName === 'telemetry') loadTelemetry();
  }

  // --- Web Speech API (Voice Dictation) ---
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    speechRecognizer = new SpeechAPI();
    speechRecognizer.continuous = true;
    speechRecognizer.interimResults = true;

    speechRecognizer.onstart = () => {
      isListening = true;
      btnMic.classList.add('listening');
      voiceStatusMsg.textContent = 'Listening... Speak your tasks clearly.';
      voiceStatusMsg.style.color = '#f43f5e';
    };

    speechRecognizer.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          intakeText.value += (intakeText.value ? ' ' : '') + event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
    };

    speechRecognizer.onerror = (e) => {
      console.warn('Speech recognition error:', e.error);
      stopListening();
    };

    speechRecognizer.onend = () => {
      stopListening();
    };
  } else {
    btnMic.title = 'Web Speech API not supported in this browser';
    btnMic.style.opacity = '0.5';
  }

  btnMic.addEventListener('click', () => {
    if (!speechRecognizer) {
      showToast('Browser does not support direct voice recognition.', 'error');
      return;
    }
    if (isListening) {
      speechRecognizer.stop();
    } else {
      speechRecognizer.start();
    }
  });

  function stopListening() {
    isListening = false;
    btnMic.classList.remove('listening');
    voiceStatusMsg.textContent = 'Voice dictation ready';
    voiceStatusMsg.style.color = 'var(--text-muted)';
  }

  // --- Intake & Decomposition ---
  btnDecompose.addEventListener('click', async () => {
    const text = intakeText.value.trim();
    if (!text) {
      showToast('Please enter or dictate a brain dump first.', 'error');
      return;
    }

    btnDecompose.disabled = true;
    decomposeSpinner.style.display = 'inline-block';

    try {
      const res = await fetch('/api/intake', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, source: 'web_dashboard' })
      });
      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error?.message || 'Failed to decompose plan.');
      }

      renderPlanPreview(data.plan, data.telemetry);
      showToast('Plan decomposed & saved successfully!', 'success');
      loadSchedule(); // Auto refresh schedule in background
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btnDecompose.disabled = false;
      decomposeSpinner.style.display = 'none';
    }
  });

  function renderPlanPreview(planPayload, telemetry) {
    const goal = planPayload.goal || {};
    const tasks = planPayload.tasks || [];

    let html = `
      <div class="preview-goal">
        <div class="preview-goal-title">🎯 Goal: ${goal.title || 'Daily Goal'}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">Timeframe: ${goal.timeframe || 'Daily'}</div>
      </div>
      <div class="preview-tasks-list">
    `;

    tasks.forEach(task => {
      const isHigh = task.priority === 'High' || task.priority_rank === 1;
      const priClass = isHigh ? 'badge-high' : (task.priority === 'Medium' ? 'badge-medium' : 'badge-low');
      const badgeText = isHigh ? 'Deep Work' : task.priority;

      html += `
        <div class="task-preview-card">
          <div class="task-preview-header">
            <span class="task-preview-title">${task.content}</span>
            <div style="display: flex; gap: 6px;">
              <span class="badge ${priClass}">${badgeText}</span>
              <span class="badge-duration">${task.remaining_minutes || task.estimated_minutes}m</span>
            </div>
          </div>
      `;

      if (task.sub_tasks && task.sub_tasks.length) {
        html += `<div class="subtasks-list">`;
        task.sub_tasks.forEach(s => {
          html += `<div>• ${s.content} (${s.estimated_minutes || 15}m)</div>`;
        });
        html += `</div>`;
      }

      html += `</div>`;
    });

    html += `</div>`;
    planPreviewContainer.innerHTML = html;
  }

  // --- Schedule Timeline ---
  async function loadSchedule() {
    timelineContainer.innerHTML = '<div class="empty-state"><p>Loading timeline...</p></div>';
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error('Could not fetch tasks');

      const scheduled = data.review?.scheduled || [];
      const pending = data.review?.pending || [];
      const allUpcoming = [...scheduled, ...pending];

      if (!allUpcoming.length) {
        timelineContainer.innerHTML = `
          <div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
            <p>No upcoming tasks scheduled for tomorrow yet. Use Intake Studio to plan your day!</p>
          </div>
        `;
        return;
      }

      let html = '';
      allUpcoming.forEach(task => {
        const isDeepWork = task.priority_rank === 1 || task.priority === 'High';
        const startStr = task.scheduled_start_at ? new Date(task.scheduled_start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Unscheduled';
        const endStr = task.scheduled_end_at ? new Date(task.scheduled_end_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        const timeDisplay = endStr ? `${startStr} - ${endStr}` : startStr;

        html += `
          <div class="timeline-item">
            <div class="timeline-time">${timeDisplay}</div>
            <div class="timeline-card ${isDeepWork ? 'deep-work' : ''}">
              <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <h3 style="font-size: 1.05rem; font-weight: 600; color: #fff;">${task.content}</h3>
                <div style="display: flex; gap: 8px;">
                  <span class="badge ${isDeepWork ? 'badge-deepwork' : 'badge-medium'}">${isDeepWork ? 'Deep Work' : task.priority}</span>
                  <span class="badge-duration">${task.remaining_minutes || task.estimated_minutes}m</span>
                </div>
              </div>
        `;

        if (task.sub_tasks && task.sub_tasks.length) {
          html += `<div class="subtasks-list">`;
          task.sub_tasks.forEach(st => {
            html += `<div>• ${st.content}</div>`;
          });
          html += `</div>`;
        }

        html += `</div></div>`;
      });

      timelineContainer.innerHTML = html;
    } catch (err) {
      timelineContainer.innerHTML = `<div class="empty-state"><p class="text-danger">${err.message}</p></div>`;
    }
  }

  btnRefreshSchedule.addEventListener('click', loadSchedule);

  btnSyncCalendar.addEventListener('click', async () => {
    btnSyncCalendar.disabled = true;
    try {
      const res = await fetch('/api/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_hour: 7, buffer_minutes: 15 })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error?.message || 'Calendar sync failed.');

      showToast(`Scheduled ${data.schedule?.scheduled?.length || 0} tasks for tomorrow!`, 'success');
      loadSchedule();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btnSyncCalendar.disabled = false;
    }
  });

  // --- Evening Review ---
  async function loadReview() {
    reviewContainer.innerHTML = '<div class="empty-state"><p>Loading tasks for review...</p></div>';
    reviewState = {};

    try {
      const res = await fetch('/api/review');
      const data = await res.json();
      const scheduled = data.review?.scheduled || [];

      if (!scheduled.length) {
        reviewContainer.innerHTML = `
          <div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            <p>No active scheduled tasks to review right now.</p>
          </div>
        `;
        return;
      }

      let html = '';
      scheduled.forEach(task => {
        reviewState[task.id] = { task_id: task.id, status: 'pending', remaining_minutes: task.remaining_minutes };

        html += `
          <div class="review-card" id="reviewCard-${task.id}">
            <div class="review-card-info">
              <h3>${task.content}</h3>
              <span style="font-size: 0.82rem; color: var(--text-muted);">Duration: ${task.remaining_minutes || task.estimated_minutes}m • Rollover count: ${task.rollover_count || 0}</span>
            </div>
            <div class="review-actions">
              <button class="btn-complete" onclick="markTaskCompleted(${task.id})">✓ Complete</button>
              <button class="btn-rollover" onclick="promptTaskRollover(${task.id})">⟳ Rollover</button>
            </div>
          </div>
        `;
      });

      reviewContainer.innerHTML = html;
    } catch (err) {
      reviewContainer.innerHTML = `<div class="empty-state"><p class="text-danger">${err.message}</p></div>`;
    }
  }

  window.markTaskCompleted = (taskId) => {
    reviewState[taskId] = { task_id: taskId, completed: true, status: 'Completed' };
    const card = document.getElementById(`reviewCard-${taskId}`);
    if (card) {
      card.className = 'review-card completed';
      card.querySelector('.review-actions').innerHTML = '<span class="badge" style="background:var(--success-bg); color:var(--success)">✓ Completed</span>';
    }
  };

  window.promptTaskRollover = (taskId) => {
    const mins = prompt('How many minutes of work are still left?', '30');
    if (mins !== null) {
      const parsed = parseInt(mins) || 30;
      reviewState[taskId] = { task_id: taskId, remaining_minutes: parsed, status: 'Pending' };
      const card = document.getElementById(`reviewCard-${taskId}`);
      if (card) {
        card.className = 'review-card rollover';
        card.querySelector('.review-actions').innerHTML = `<span class="badge" style="background:var(--warning-bg); color:var(--warning)">⟳ Rolled over (${parsed}m)</span>`;
      }
    }
  };

  btnSaveReview.addEventListener('click', async () => {
    const updates = Object.values(reviewState);
    if (!updates.length) {
      showToast('No task updates to submit.', 'info');
      return;
    }

    try {
      const res = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates })
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error('Failed to apply review updates.');

      showToast(`Review complete! Updated ${data.review?.count || updates.length} tasks.`, 'success');
      loadReview();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // --- Idea Inbox ---
  async function loadIdeas() {
    ideasGrid.innerHTML = '<div class="empty-state"><p>Loading ideas...</p></div>';
    try {
      const res = await fetch('/api/ideas');
      const data = await res.json();
      const ideas = data.ideas || [];

      if (!ideas.length) {
        ideasGrid.innerHTML = '<div class="empty-state"><p>Your idea inbox is empty. Capture thoughts above!</p></div>';
        return;
      }

      let html = '';
      ideas.forEach(idea => {
        const timeStr = idea.created_at ? new Date(idea.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
        html += `
          <div class="idea-card">
            <div class="idea-card-content">${idea.content}</div>
            <div class="idea-card-footer">
              <span>${timeStr}</span>
              <button class="btn-secondary btn-sm" onclick="convertIdeaToPlan('${encodeURIComponent(idea.content)}')">Plan This</button>
            </div>
          </div>
        `;
      });

      ideasGrid.innerHTML = html;
    } catch (err) {
      ideasGrid.innerHTML = `<div class="empty-state"><p class="text-danger">${err.message}</p></div>`;
    }
  }

  btnSaveIdea.addEventListener('click', async () => {
    const text = quickIdeaInput.value.trim();
    if (!text) return;

    try {
      const res = await fetch('/api/ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, source: 'web_quick_capture' })
      });
      if (!res.ok) throw new Error('Could not save idea.');

      quickIdeaInput.value = '';
      showToast('Idea captured into inbox!', 'success');
      loadIdeas();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  quickIdeaInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') btnSaveIdea.click();
  });

  window.convertIdeaToPlan = (encodedText) => {
    const text = decodeURIComponent(encodedText);
    intakeText.value = text;
    switchTab('intake');
    showToast('Idea loaded into Intake Studio. Click "Decompose & Plan" to generate schedule.', 'info');
  };

  // --- Telemetry Dashboard ---
  async function loadTelemetry() {
    try {
      const res = await fetch('/api/telemetry');
      const data = await res.json();
      const stats = data.telemetry || {};

      document.getElementById('statAvgLatency').textContent = `${stats.avg_latency_ms || 0} ms`;
      document.getElementById('statSuccessRate').textContent = `${stats.success_rate || 100}%`;
      document.getElementById('statTotalCalls').textContent = stats.total_calls || 0;

      const tbody = document.getElementById('telemetryTableBody');
      const traces = stats.recent_logs || [];

      if (!traces.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No telemetry traces recorded yet.</td></tr>';
        return;
      }

      let html = '';
      traces.forEach(t => {
        const timeStr = t.created_at ? new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
        const isErr = t.status === 'error';
        html += `
          <tr>
            <td>${timeStr}</td>
            <td><strong>${t.operation}</strong></td>
            <td>${t.model || 'N/A'}</td>
            <td>${t.latency_ms} ms</td>
            <td>${t.prompt_tokens || 0} in / ${t.completion_tokens || 0} out</td>
            <td><span class="badge ${isErr ? 'badge-high' : 'badge-duration'}" style="${!isErr ? 'color:var(--success)' : ''}">${t.status}</span></td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      console.warn('Telemetry fetch failed:', err);
    }
  }

  btnRefreshTelemetry.addEventListener('click', loadTelemetry);

  // --- Initial System Health Check ---
  async function checkSystemHealth() {
    try {
      const res = await fetch('/api/readiness');
      const data = await res.json();
      if (data.mode) {
        dbStatusText.textContent = data.mode === 'sqlite' ? 'SQLite Local' : 'Supabase';
      }
      if (data.calendar_connected) {
        calDot.className = 'status-dot dot-green';
        calStatusText.textContent = 'Calendar Linked';
      } else {
        calDot.className = 'status-dot dot-amber';
        calStatusText.textContent = 'Calendar (Offline)';
      }
    } catch (e) {
      dbStatusText.textContent = 'SQLite Ready';
    }
  }

  checkSystemHealth();
});
