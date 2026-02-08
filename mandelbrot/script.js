const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const iterInput = document.getElementById('iter');
const renderBtn = document.getElementById('renderBtn');
const resetBtn = document.getElementById('resetBtn');
const fitBtn = document.getElementById('fitBtn');
const coordsEl = document.getElementById('coords');

let width = 800;
let height = 600;
let deviceScale = Math.max(1, window.devicePixelRatio || 1);

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(200, Math.floor(rect.width));
  height = Math.max(200, Math.floor(rect.height || Math.round(rect.width * 3/4)));
  canvas.width = Math.floor(width * deviceScale);
  canvas.height = Math.floor(height * deviceScale);
  canvas.style.height = height + 'px';
}

let state = {
  xCenter: -0.5,
  yCenter: 0.0,
  scale: 1.5,
};

function fitToCanvas() {
  state = { xCenter: -0.5, yCenter: 0.0, scale: 1.5 };
}

fitToCanvas();
window.addEventListener('resize', () => { resizeCanvas(); render(); });

// Color mapping similar to Python version
function colorFromNorm(norm) {
  // norm in [0,1]
  const n = Math.sqrt(norm);
  const r = Math.round(255 * Math.min(1, Math.max(0, 3 * (1 - n))));
  const g = Math.round(255 * Math.min(1, Math.max(0, 3 * Math.abs(n - 0.5))));
  const b = Math.round(255 * Math.min(1, Math.max(0, 3 * n)));
  return [r, g, b, 255];
}

function render() {
  resizeCanvas();
  const maxIter = parseInt(iterInput.value, 10) || 200;
  const img = ctx.createImageData(canvas.width, canvas.height);
  const data = img.data;

  const xMin = state.xCenter - state.scale;
  const xMax = state.xCenter + state.scale;
  const yScale = state.scale * canvas.height / canvas.width;
  const yMin = state.yCenter - yScale;
  const yMax = state.yCenter + yScale;

  const w = canvas.width;
  const h = canvas.height;

  let row = 0;
  const chunk = 8; // rows per chunk

  function renderChunk() {
    const end = Math.min(h, row + chunk);
    for (let j = row; j < end; j++) {
      const y0 = yMin + (yMax - yMin) * j / (h - 1);
      for (let i = 0; i < w; i++) {
        const x0 = xMin + (xMax - xMin) * i / (w - 1);
        let x = 0.0, y = 0.0, iteration = 0;
        while (x*x + y*y <= 4.0 && iteration < maxIter) {
          const xtemp = x*x - y*y + x0;
          y = 2.0 * x * y + y0;
          x = xtemp;
          iteration++;
        }
        const idx = (j * w + i) * 4;
        const norm = iteration / maxIter;
        const [r,g,b,a] = colorFromNorm(norm);
        data[idx] = r;
        data[idx+1] = g;
        data[idx+2] = b;
        data[idx+3] = a;
      }
    }
    row = end;
    ctx.putImageData(img, 0, 0);
    if (row < h) {
      // allow UI updates
      setTimeout(renderChunk, 0);
    }
  }
  renderChunk();
}

renderBtn.addEventListener('click', render);
resetBtn.addEventListener('click', () => { fitToCanvas(); render(); });
fitBtn.addEventListener('click', () => { fitToCanvas(); render(); });

// Interaction: pan and zoom
let dragging = false;
let lastX = 0, lastY = 0;

canvas.addEventListener('mousedown', (e) => {
  dragging = true;
  lastX = e.clientX;
  lastY = e.clientY;
});
window.addEventListener('mouseup', () => { dragging = false; });
window.addEventListener('mousemove', (e) => {
  if (!dragging) return;
  const dx = e.clientX - lastX;
  const dy = e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  // translate by pixel deltas
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  state.xCenter -= dx / w * (2 * state.scale);
  state.yCenter += dy / h * (2 * state.scale * h / w);
  render();
});

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  // zoom toward mouse pointer
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;
  const my = (e.clientY - rect.top) / rect.height;
  const xMin = state.xCenter - state.scale;
  const xMax = state.xCenter + state.scale;
  const yScale = state.scale * rect.height / rect.width;
  const yMin = state.yCenter - yScale;
  const yMax = state.yCenter + yScale;
  const cx = xMin + (xMax - xMin) * mx;
  const cy = yMin + (yMax - yMin) * my;

  const zoom = e.deltaY > 0 ? 1.2 : 1/1.2;
  state.scale *= zoom;
  // move center so point under cursor stays fixed
  state.xCenter = cx + (state.xCenter - cx) * zoom;
  state.yCenter = cy + (state.yCenter - cy) * zoom;
  render();
}, { passive: false });

canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;
  const my = (e.clientY - rect.top) / rect.height;
  const xMin = state.xCenter - state.scale;
  const xMax = state.xCenter + state.scale;
  const yScale = state.scale * rect.height / rect.width;
  const yMin = state.yCenter - yScale;
  const yMax = state.yCenter + yScale;
  const cx = xMin + (xMax - xMin) * mx;
  const cy = yMin + (yMax - yMin) * my;
  state.xCenter = cx; state.yCenter = cy;
  state.scale *= 0.5;
  render();
});

// show coordinates on move
canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / rect.width;
  const my = (e.clientY - rect.top) / rect.height;
  const xMin = state.xCenter - state.scale;
  const xMax = state.xCenter + state.scale;
  const yScale = state.scale * rect.height / rect.width;
  const yMin = state.yCenter - yScale;
  const yMax = state.yCenter + yScale;
  const cx = xMin + (xMax - xMin) * mx;
  const cy = yMin + (yMax - yMin) * my;
  coordsEl.textContent = `x=${cx.toFixed(6)}, y=${cy.toFixed(6)}, scale=${state.scale.toExponential(3)}`;
});

// initial sizing and render
resizeCanvas();
render();
