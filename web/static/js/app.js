/* ============================================================
   Swiss Precision — Detection Lab
   ============================================================ */

// ── DOM refs ───────────────────────────────────────────
const $ = (s, p) => (p || document).querySelector(s);
const $$ = (s, p) => [...(p || document).querySelectorAll(s)];

// ── State ──────────────────────────────────────────────
const state = {
  detectFile: null,
  batchFiles: [],
  videoFile: null,
};

// ── Tab switching ──────────────────────────────────────
function initTabs() {
  const bar = $('#tabBar');
  const btns = $$('.tab-btn', bar);
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      $$('.tab-panel').forEach(p => p.classList.remove('active'));
      $(`#panel-${tab}`).classList.add('active');
      if (tab === 'info') loadModelInfo();
    });
  });
}

// ── Loading overlay ────────────────────────────────────
function showLoading() { $('#loadingOverlay').classList.add('active'); }
function hideLoading() { $('#loadingOverlay').classList.remove('active'); }

// ── Upload zone helpers ────────────────────────────────
function setupUploadZone(zoneId, inputId, promptId, onFile) {
  const zone = $(zoneId);
  const input = $(inputId);
  const prompt = $(promptId);

  zone.addEventListener('click', () => input.click());

  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) {
      if (input.multiple) {
        input.files = files;
        onFile([...files]);
      } else {
        const dt = new DataTransfer();
        dt.items.add(files[0]);
        input.files = dt.files;
        onFile(files[0]);
      }
    }
  });

  input.addEventListener('change', () => {
    if (input.files.length) {
      if (input.multiple) onFile([...input.files]);
      else onFile(input.files[0]);
    }
  });
}

// ── Detect tab ─────────────────────────────────────────
function initDetectTab() {
  const zone = $('#uploadZone');
  const input = $('#fileInput');
  const preview = $('#uploadPreview');
  const prompt = $('#uploadPrompt');
  const btn = $('#detectBtn');
  const confS = $('#confSlider');
  const confV = $('#confVal');
  const output = $('#detectOutput');

  confS.addEventListener('input', () => { confV.textContent = parseFloat(confS.value).toFixed(2); });

  setupUploadZone('#uploadZone', '#fileInput', '#uploadPrompt', file => {
    state.detectFile = file;
    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.onload = () => URL.revokeObjectURL(url);
    zone.classList.add('has-file');
    btn.disabled = false;
  });

  btn.addEventListener('click', async () => {
    if (!state.detectFile) return;
    showLoading();
    btn.disabled = true;
    btn.textContent = 'Detecting…';
    output.innerHTML = '';

    try {
      const fd = new FormData();
      fd.append('file', state.detectFile);
      fd.append('conf', confS.value);
      fd.append('imgsz', $('#imgszSelect').value);

      const res = await fetch('/api/detect', { method: 'POST', body: fd });
      if (!res.ok) { throw new Error(`Server ${res.status}`); }
      const data = await res.json();
      if (data.error) { throw new Error(data.error); }

      renderDetectResult(output, data);
    } catch (err) {
      output.innerHTML = `<div class="output-placeholder"><p class="error-text">${err.message}</p></div>`;
    } finally {
      hideLoading();
      btn.disabled = false;
      btn.textContent = 'Run Detection';
    }
  });
}

function renderDetectResult(container, data) {
  const imgUrl = data.image_url + '?t=' + Date.now();
  let html = '';

  if (data.stats.total === 0) {
    html += `<div class="result-stat">No objects<br><span>detected</span></div>`;
    html += `<div class="result-stat-label">Try lowering the confidence threshold</div>`;
    html += `<img class="result-image" src="${imgUrl}" alt="Annotated result">`;
  } else {
    html += `<div class="result-stat"><span>${data.stats.total}</span> objects<br>across <span>${data.stats.classes}</span> classes</div>`;
    html += `<div class="result-stat-label">Detection complete</div>`;
    html += `<img class="result-image" src="${imgUrl}" alt="Annotated result">`;
    html += renderTable(data.detections);
  }
  container.innerHTML = html;
}

function renderTable(detections) {
  let h = '<table class="result-table"><thead><tr><th>Class</th><th>Conf.</th><th>Bbox</th></tr></thead><tbody>';
  for (const d of detections) {
    const b = d.bbox;
    h += `<tr><td>${d.class}</td><td class="conf-cell">${d.confidence.toFixed(3)}</td><td>${b[0]}, ${b[1]}, ${b[2]}, ${b[3]}</td></tr>`;
  }
  h += '</tbody></table>';
  return h;
}

// ── Batch tab ──────────────────────────────────────────
function initBatchTab() {
  const zone = $('#batchUploadZone');
  const input = $('#batchFileInput');
  const previewDiv = $('#batchPreviews');
  const btn = $('#batchDetectBtn');
  const confS = $('#batchConf');
  const confV = $('#batchConfVal');
  const output = $('#batchOutput');

  confS.addEventListener('input', () => { confV.textContent = parseFloat(confS.value).toFixed(2); });

  setupUploadZone('#batchUploadZone', '#batchFileInput', '#batchUploadPrompt', files => {
    state.batchFiles = files;
    previewDiv.innerHTML = '';
    files.forEach(f => {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(f);
      img.onload = () => URL.revokeObjectURL(img.src);
      previewDiv.appendChild(img);
    });
    zone.classList.add('has-file');
    btn.disabled = false;
  });

  btn.addEventListener('click', async () => {
    if (!state.batchFiles.length) return;
    showLoading();
    btn.disabled = true;
    btn.textContent = 'Processing…';
    output.innerHTML = '';

    try {
      const fd = new FormData();
      state.batchFiles.forEach(f => fd.append('files', f));
      fd.append('conf', confS.value);
      fd.append('imgsz', $('#batchImgsz').value);

      const res = await fetch('/api/detect/batch', { method: 'POST', body: fd });
      if (!res.ok) throw new Error(`Server ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      renderBatchResult(output, data.results);
    } catch (err) {
      output.innerHTML = `<div class="output-placeholder"><p class="error-text">${err.message}</p></div>`;
    } finally {
      hideLoading();
      btn.disabled = false;
      btn.textContent = 'Run Batch Detection';
    }
  });
}

function renderBatchResult(container, results) {
  let html = '<div class="gallery-grid">';
  for (const r of results) {
    if (r.error) {
      html += `<div class="gallery-item"><div class="gallery-caption">${r.filename}: ${r.error}</div></div>`;
    } else {
      html += `<div class="gallery-item">`;
      html += `<img src="${r.image_url}?t=${Date.now()}" alt="${r.filename}">`;
      html += `<div class="gallery-caption">${r.filename} — ${r.count} objects</div>`;
      html += `</div>`;
    }
  }
  html += '</div>';
  container.innerHTML = html;
}

// ── Camera tab (real-time WebSocket + canvas) ──────────
function initCameraTab() {
  const video = $('#cameraVideo');
  const canvas = $('#cameraCanvas');
  const ctx = canvas.getContext('2d');
  const viewfinder = $('#cameraViewfinder');
  const startBtn = $('#cameraStartBtn');
  const confS = $('#cameraConf');
  const confV = $('#cameraConfVal');
  const imgszSel = $('#cameraImgsz');
  const hudFps = $('#hudFps');
  const hudCount = $('#hudCount');
  const hudLatency = $('#hudLatency');

  let stream = null;
  let ws = null;
  let animId = null;
  let latestDetections = [];
  let latestFrameW = 640;
  let latestFrameH = 360;
  let waiting = false;
  let fpsFrames = 0;
  let fpsLast = performance.now();
  let latencyMs = 0;
  let sendTime = 0;

  confS.addEventListener('input', () => {
    confV.textContent = parseFloat(confS.value).toFixed(2);
    sendConfig();
  });
  imgszSel.addEventListener('change', sendConfig);

  function sendConfig() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'config',
        conf: parseFloat(confS.value),
        imgsz: parseInt(imgszSel.value),
      }));
    }
  }

  function connectWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/ws/detect`);
    ws.onopen = () => { hudLatency.textContent = '-- ms'; };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.error) { console.error(data.error); return; }
        // Round-trip latency: send → receive
        if (sendTime > 0) {
          latencyMs = Math.round(performance.now() - sendTime);
          sendTime = 0;
        }
        latestDetections = data.detections || [];
        latestFrameW = data.frame_w || latestFrameW;
        latestFrameH = data.frame_h || latestFrameH;
        waiting = false;
      } catch (_) {}
    };
    ws.onclose = () => { hudLatency.textContent = 'offline'; };
    ws.onerror = () => { hudLatency.textContent = 'error'; };
  }

  function disconnectWS() {
    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    waiting = false;
  }

  // Start / stop camera
  startBtn.addEventListener('click', async () => {
    if (stream) {
      stopCamera();
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' }
      });
      video.srcObject = stream;
      await video.play();

      // Wait for video metadata
      await new Promise(r => { if (video.videoWidth) r(); else video.addEventListener('loadedmetadata', r, { once: true }); });

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      viewfinder.classList.add('live');
      startBtn.textContent = 'Stop Camera';
      startBtn.style.background = 'var(--accent)';
      hudFps.textContent = '-- FPS';
      hudCount.textContent = '0 objects';

      connectWS();
      sendConfig();

      // Start render loop
      fpsFrames = 0;
      fpsLast = performance.now();
      latestDetections = [];
      animId = requestAnimationFrame(loop);
    } catch (err) {
      viewfinder.classList.remove('live');
      hudFps.textContent = `Error: ${err.message}`;
    }
  });

  function stopCamera() {
    if (animId) { cancelAnimationFrame(animId); animId = null; }
    disconnectWS();
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    video.srcObject = null;
    viewfinder.classList.remove('live');
    startBtn.textContent = 'Start Camera';
    startBtn.style.background = '';
    hudFps.textContent = '-- FPS';
    hudCount.textContent = '0 objects';
    hudLatency.textContent = '';
    latencyMs = 0;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  function loop(now) {
    if (!stream) return;
    animId = requestAnimationFrame(loop);

    const vw = video.videoWidth;
    const vh = video.videoHeight;
    if (!vw || !vh) return;

    // Resize canvas if video dimensions change
    if (canvas.width !== vw || canvas.height !== vh) {
      canvas.width = vw;
      canvas.height = vh;
    }

    // Draw camera frame
    ctx.drawImage(video, 0, 0, vw, vh);

    // Draw detection boxes
    if (latestDetections.length && latestFrameW && latestFrameH) {
      const sx = vw / latestFrameW;
      const sy = vh / latestFrameH;

      for (const det of latestDetections) {
        const [x1, y1, x2, y2] = det.bbox;
        const bx = x1 * sx;
        const by = y1 * sy;
        const bw = (x2 - x1) * sx;
        const bh = (y2 - y1) * sy;

        // Box
        ctx.strokeStyle = '#e02020';
        ctx.lineWidth = Math.max(2, vw / 500);
        ctx.strokeRect(bx, by, bw, bh);

        // Label background
        const label = `${det.class} ${det.confidence.toFixed(2)}`;
        ctx.font = `500 ${Math.max(11, vw / 80)}px 'DM Mono', 'Consolas', monospace`;
        const metrics = ctx.measureText(label);
        const lh = Math.max(16, vw / 55);
        ctx.fillStyle = 'rgba(224, 32, 32, 0.85)';
        ctx.fillRect(bx, by - lh, metrics.width + 8, lh);

        // Label text
        ctx.fillStyle = '#fff';
        ctx.fillText(label, bx + 4, by - 4);
      }
    }

    // FPS counter
    fpsFrames++;
    if (now - fpsLast >= 1000) {
      const fps = Math.round(fpsFrames / ((now - fpsLast) / 1000));
      hudFps.textContent = `${fps} FPS`;
      fpsFrames = 0;
      fpsLast = now;
    }

    // Object count & latency
    hudCount.textContent = `${latestDetections.length} objects`;
    hudLatency.textContent = latencyMs > 0 ? `${latencyMs} ms` : '-- ms';

    // Send frame to backend via WebSocket
    if (!waiting && ws && ws.readyState === WebSocket.OPEN) {
      waiting = true;
      const sendW = parseInt(imgszSel.value);
      const sendH = Math.round(vh * sendW / vw);

      // Use a small offscreen canvas for the send frame
      const off = document.createElement('canvas');
      off.width = sendW;
      off.height = sendH;
      off.getContext('2d').drawImage(video, 0, 0, sendW, sendH);

      off.toBlob(blob => {
        if (ws && ws.readyState === WebSocket.OPEN && blob) {
          sendTime = performance.now();
          ws.send(blob);
        } else {
          waiting = false;
        }
      }, 'image/jpeg', 0.65);
    }
  }

  // Clean up when leaving camera tab
  const cameraPanel = $('#panel-camera');
  const observer = new MutationObserver(() => {
    if (!cameraPanel.classList.contains('active') && stream) {
      stopCamera();
    }
  });
  observer.observe(cameraPanel, { attributes: true, attributeFilter: ['class'] });
}

// ── Video tab ──────────────────────────────────────────
function initVideoTab() {
  const zone = $('#videoUploadZone');
  const input = $('#videoFileInput');
  const preview = $('#videoPreview');
  const prompt = $('#videoUploadPrompt');
  const btn = $('#videoDetectBtn');
  const confS = $('#videoConf');
  const confV = $('#videoConfVal');
  const output = $('#videoOutput');

  confS.addEventListener('input', () => { confV.textContent = parseFloat(confS.value).toFixed(2); });

  setupUploadZone('#videoUploadZone', '#videoFileInput', '#videoUploadPrompt', file => {
    state.videoFile = file;
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    prompt.style.display = 'none';
    zone.classList.add('has-file');
    btn.disabled = false;
  });

  btn.addEventListener('click', async () => {
    if (!state.videoFile) return;
    showLoading();
    btn.disabled = true;
    btn.textContent = 'Processing video…';
    output.innerHTML = '';

    try {
      const fd = new FormData();
      fd.append('file', state.videoFile);
      fd.append('conf', confS.value);
      fd.append('imgsz', $('#videoImgsz').value);

      const res = await fetch('/api/detect/video', { method: 'POST', body: fd });
      if (!res.ok) throw new Error(`Server ${res.status}`);
      const data = await res.json();
      if (data.error) throw new Error(data.error);

      renderVideoResult(output, data.video_url);
    } catch (err) {
      output.innerHTML = `<div class="output-placeholder"><p class="error-text">${err.message}</p></div>`;
    } finally {
      hideLoading();
      btn.disabled = false;
      btn.textContent = 'Run Video Detection';
    }
  });
}

function renderVideoResult(container, url) {
  const fullUrl = url + '?t=' + Date.now();
  container.innerHTML = `
    <video class="result-video" src="${fullUrl}" controls playsinline preload="auto"
           style="width:100%;max-height:480px;background:#1a1a1a;border-radius:3px;">
    </video>
    <p style="margin-top:12px;text-align:center;font-family:var(--font-mono);font-size:0.75rem;color:var(--text-dim);">
      <a href="${fullUrl}" download style="color:var(--text);text-decoration:underline;">Download video</a>
    </p>
  `;
}

// ── Model info tab ─────────────────────────────────────
async function loadModelInfo() {
  const card = $('#infoCard');
  card.innerHTML = '<div class="output-placeholder"><p>Loading…</p></div>';
  try {
    const res = await fetch('/api/model');
    if (!res.ok) throw new Error(`Server ${res.status}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const tags = data.classes.map(c => `<span class="class-tag">${c}</span>`).join('');
    card.innerHTML = `
      <h2>Model Information</h2>
      <div class="info-row">
        <span class="info-label">Weights</span>
        <span class="info-value">${data.weights}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Classes</span>
        <span class="info-value">${data.num_classes}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Class List</span>
        <div class="class-tags">${tags}</div>
      </div>
    `;
  } catch (err) {
    card.innerHTML = `<div class="output-placeholder"><p class="error-text">${err.message}</p></div>`;
  }
}

// ── Model status check ─────────────────────────────────
async function checkModelStatus() {
  const el = $('#modelStatus');
  try {
    const res = await fetch('/api/model');
    if (res.ok) {
      el.innerHTML = '● Model Ready';
      el.style.color = '';
    } else {
      el.innerHTML = '○ Model Offline';
      el.style.color = 'var(--accent)';
    }
  } catch {
    el.innerHTML = '○ Model Offline';
    el.style.color = 'var(--accent)';
  }
}

// ── Init ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initDetectTab();
  initCameraTab();
  initBatchTab();
  initVideoTab();
  checkModelStatus();
});
