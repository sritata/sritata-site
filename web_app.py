#!/usr/bin/env python3
"""Minimal Flask web app to run the mandelbrot generator interactively."""
from io import BytesIO
from flask import Flask, request, send_file, render_template_string, jsonify
import mandelbrot
import numpy as np
import zoom_mode
import os
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder='site', template_folder='site')

INDEX_HTML = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Mandelbrot Interactive</title>
  <style>body{font-family:Arial,sans-serif;padding:12px} .controls{display:flex;gap:8px;flex-wrap:wrap} label{display:block;font-size:0.9rem} input{width:120px}</style>
  </head>
<body>
  <h1>Mandelbrot Interactive</h1>
  <div class="controls">
    <div>
      <label>Width <input id="width" type="number" value="800"></label>
      <label>Height <input id="height" type="number" value="600"></label>
    </div>
    <div>
      <label>Max Iter <input id="max_iter" type="number" value="300"></label>
      <label>Scale <input id="scale" type="text" value="1.5"></label>
    </div>
    <div>
      <label>X Center <input id="x_center" type="text" value="-0.5"></label>
      <label>Y Center <input id="y_center" type="text" value="0.0"></label>
    </div>
    <div style="align-self:end">
      <button id="render">Render</button>
    </div>
  </div>
  <p id="status"></p>
  <div><img id="img" src="" alt="mandelbrot" style="max-width:100%;border:1px solid #ccc"></div>

  <script>
    const btn = document.getElementById('render');
    const img = document.getElementById('img');
    const status = document.getElementById('status');

    let busy = false;
    function renderFromFields(){
      if(busy) return;
      busy = true;
      btn.disabled = true;
      const width = Number(document.getElementById('width').value);
      const height = Number(document.getElementById('height').value);
      const max_iter = Number(document.getElementById('max_iter').value);
      const scale = document.getElementById('scale').value;
      const x_center = document.getElementById('x_center').value;
      const y_center = document.getElementById('y_center').value;
      const q = new URLSearchParams({ width, height, max_iter, scale, x_center, y_center });
      #!/usr/bin/env python3
      """Minimal Flask web app to run the mandelbrot generator interactively."""
      from io import BytesIO
      from flask import Flask, request, send_file, render_template_string, jsonify
      import mandelbrot
      import numpy as np
      import zoom_mode
      import os
      from PIL import Image, ImageDraw, ImageFont

      app = Flask(__name__, static_folder='site', template_folder='site')

      INDEX_HTML = '''
      <!doctype html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <title>Mandelbrot Interactive</title>
        <style>body{font-family:Arial,sans-serif;padding:12px} .controls{display:flex;gap:8px;flex-wrap:wrap} label{display:block;font-size:0.9rem} input{width:120px}</style>
        </head>
      <body>
        <h1>Mandelbrot Interactive</h1>
        <div class="controls">
          <div>
            <label>Width <input id="width" type="number" value="800"></label>
            <label>Height <input id="height" type="number" value="600"></label>
          </div>
          <div>
            <label>Max Iter <input id="max_iter" type="number" value="300"></label>
            <label>Scale <input id="scale" type="text" value="1.5"></label>
          </div>
          <div>
            <label>X Center <input id="x_center" type="text" value="-0.5"></label>
            <label>Y Center <input id="y_center" type="text" value="0.0"></label>
          </div>
          <div style="align-self:end">
            <button id="render">Render</button>
          </div>
        </div>
        <p id="status"></p>
        <div><img id="img" src="" alt="mandelbrot" style="max-width:100%;border:1px solid #ccc"></div>

        <script>
          const btn = document.getElementById('render');
          const img = document.getElementById('img');
          const status = document.getElementById('status');

          let busy = false;
          function renderFromFields(){
            if(busy) return;
            busy = true;
            btn.disabled = true;
            const width = Number(document.getElementById('width').value);
            const height = Number(document.getElementById('height').value);
            const max_iter = Number(document.getElementById('max_iter').value);
            const scale = document.getElementById('scale').value;
            const x_center = document.getElementById('x_center').value;
            const y_center = document.getElementById('y_center').value;
            const q = new URLSearchParams({ width, height, max_iter, scale, x_center, y_center });
            const url = '/render?' + q.toString();
            status.textContent = 'Rendering...';
            img.src = url + '&_=' + Date.now();
            img.onload = ()=>{ status.textContent = 'Rendered'; busy=false; btn.disabled=false; };
            img.onerror = ()=>{ status.textContent = 'Render failed'; busy=false; btn.disabled=false; };
          }

          btn.addEventListener('click', ()=>{ renderFromFields(); });

          // Click-to-zoom: map click pixel -> complex, adjust scale and iterations, then re-render
          img.addEventListener('click', function(ev){
            if(busy) return; // ignore clicks while rendering
            if(!img.naturalWidth || !img.naturalHeight) return;
            const rect = img.getBoundingClientRect();
            // pixel coordinates in image space
            const px = (ev.clientX - rect.left) * (img.naturalWidth / rect.width);
            const py = (ev.clientY - rect.top) * (img.naturalHeight / rect.height);

            // read current params
            const width = Number(document.getElementById('width').value);
            const height = Number(document.getElementById('height').value);
            let scale = Number(document.getElementById('scale').value);
            let x_center = Number(document.getElementById('x_center').value);
            let y_center = Number(document.getElementById('y_center').value);

            // compute complex coordinates using same math as _pixel_to_complex
            const x_min = x_center - scale;
            const x_max = x_center + scale;
            const y_scale = scale * height / width;
            const y_min = y_center - y_scale;
            const y_max = y_center + y_scale;

            const x = x_min + (x_max - x_min) * px / Math.max(1, (width - 1));
            const y = y_min + (y_max - y_min) * py / Math.max(1, (height - 1));

            // update center to clicked point and zoom in 4x
            x_center = x;
            y_center = y;
            scale = scale * 0.25;

            // increase iterations by ~25% to keep detail
            const maxIterEl = document.getElementById('max_iter');
            const newMax = Math.max(10, Math.min(2000, Math.floor(Number(maxIterEl.value) * 1.25)));
            maxIterEl.value = newMax;

            // write updated params back to the form
            document.getElementById('x_center').value = x_center;
            document.getElementById('y_center').value = y_center;
            document.getElementById('scale').value = scale;

            // trigger render
            renderFromFields();
          });
        </script>
      </body>
      </html>
      '''


      @app.route('/')
      def index():
          return render_template_string(INDEX_HTML)


      @app.route('/render')
      def render_image():
          # read params with safe defaults
          try:
              width = int(request.args.get('width', 800))
              height = int(request.args.get('height', 600))
              max_iter = int(request.args.get('max_iter', 300))
              x_center = float(request.args.get('x_center', -0.5))
              y_center = float(request.args.get('y_center', 0.0))
              scale = float(request.args.get('scale', 1.5))
          except Exception:
              return 'Bad parameters', 400

          # clamp sizes to avoid DoS
          width = max(50, min(2000, width))
          height = max(50, min(2000, height))
          max_iter = max(10, min(20000, max_iter))

          div = mandelbrot.mandelbrot(width, height, max_iter, x_center, y_center, scale)
          arr = mandelbrot.color_map(div, max_iter)
          im = Image.fromarray(arr, mode='RGB')
          # draw a bracket-style scale overlay on the rendered image
          try:
            draw = ImageDraw.Draw(im, 'RGBA')
            w, h = im.size
            bar_w = max(12, int(w * 0.045))
            padding = max(8, int(w * 0.02))
            left = w - bar_w - padding
            right = w - padding
            top = padding
            bottom = h - padding
            thickness = max(2, int(bar_w * 0.25))
            # bracket lines
            draw.line([(left, top), (right, top)], fill=(255, 255, 255, 220), width=thickness)
            draw.line([(right, top), (right, bottom)], fill=(255, 255, 255, 220), width=thickness)
            draw.line([(left, bottom), (right, bottom)], fill=(255, 255, 255, 220), width=thickness)
            # label
            try:
              from PIL import ImageFont
              font_size = max(12, int(h * 0.04))
              try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
              except Exception:
                try:
                  font = ImageFont.truetype("Arial.ttf", font_size)
                except Exception:
                  font = ImageFont.load_default()
              label = f"{float(scale):.2e}"
              text_x = left - (bar_w + 40)
              text_y = top + 6
              try:
                draw.text((text_x, text_y), label, font=font, fill=(255,255,255,255))
              except Exception:
                draw.text((text_x, text_y), label, fill=(255,255,255,255))
            except Exception:
              pass
          except Exception:
            pass
          buf = BytesIO()
          im.save(buf, format='PNG')
          buf.seek(0)
          return send_file(buf, mimetype='image/png')


      if __name__ == '__main__':
          app.run(host='0.0.0.0', port=5000, debug=True)
