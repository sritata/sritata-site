(function () {
  const cfgEl = document.getElementById('mandel-config');
  if (!cfgEl) return;

  const cfg = JSON.parse(cfgEl.textContent);
  const form = document.getElementById('controls');
  const img = document.getElementById('img');
  const status = document.getElementById('status');

  if (!form || !img) return;

  // Helper: get a form field by name
  const field = (name) => form.querySelector(`[name="${name}"]`);

  // Helper: submit as GET to pageEndpoint (full page reload)
  function submitRender() {
    status && (status.textContent = 'Rendering...');
    // Ensure form submits to the endpoint we want
    form.action = cfg.pageEndpoint;
    form.method = 'get';
    form.submit();
  }

  // Zoom on click: update fields then submit
  img.addEventListener('click', function (ev) {
    if (!img.naturalWidth || !img.naturalHeight) return;

    const rect = img.getBoundingClientRect();
    const px = (ev.clientX - rect.left) * (img.naturalWidth / rect.width);
    const py = (ev.clientY - rect.top) * (img.naturalHeight / rect.height);

    const width = Number(field('width').value);
    const height = Number(field('height').value);

    let scale = Number(field('scale').value);
    let x_center = Number(field('x_center').value);
    let y_center = Number(field('y_center').value);

    const x_min = x_center - scale;
    const x_max = x_center + scale;

    const y_scale = scale * height / width;
    const y_min = y_center - y_scale;
    const y_max = y_center + y_scale;

    const x = x_min + (x_max - x_min) * px / Math.max(1, (width - 1));
    const y = y_min + (y_max - y_min) * py / Math.max(1, (height - 1));

    x_center = x;
    y_center = y;
    scale = scale * (cfg.zoomFactor ?? 0.25);

    // grow iterations modestly
    const maxIterEl = field('max_iter');
    const newMax = Math.max(
      cfg.iterMin ?? 10,
      Math.min(cfg.iterMax ?? 2000, Math.floor(Number(maxIterEl.value) * (cfg.iterGrow ?? 1.25)))
    );

    field('x_center').value = x_center;
    field('y_center').value = y_center;
    field('scale').value = scale;
    maxIterEl.value = newMax;

    submitRender();
  });

  // Optional: if you still want the status cleared on load
  window.addEventListener('load', () => {
    status && (status.textContent = '');
  });
})();
