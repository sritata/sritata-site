"""Vercel serverless function for Mandelbrot rendering."""
from urllib.parse import parse_qs
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
import base64


def mandelbrot(width, height, max_iter, x_center, y_center, scale):
    """Compute Mandelbrot set iteration counts."""
    div_time = np.empty((height, width), dtype=np.int32)
    
    x_min = x_center - scale
    x_max = x_center + scale
    y_scale = scale * height / width
    y_min = y_center - y_scale
    y_max = y_center + y_scale
    
    for j in range(height):
        y0 = y_min + (y_max - y_min) * j / max(1, (height - 1))
        for i in range(width):
            x0 = x_min + (x_max - x_min) * i / max(1, (width - 1))
            x = 0.0
            y = 0.0
            iteration = 0
            while x*x + y*y <= 4.0 and iteration < max_iter:
                xtemp = x*x - y*y + x0
                y = 2.0 * x * y + y0
                x = xtemp
                iteration += 1
            div_time[j, i] = iteration
    
    return div_time


def color_map(div_time, max_iter):
    """Map iteration counts to RGB colors."""
    norm = div_time.astype(float) / max_iter
    norm = np.sqrt(norm)
    r = np.uint8(255 * np.clip(3 * (1 - norm), 0, 1))
    g = np.uint8(255 * np.clip(3 * np.abs(norm - 0.5), 0, 1))
    b = np.uint8(255 * np.clip(3 * norm, 0, 1))
    rgb = np.dstack((r, g, b))
    return rgb


def handler(request):
    """Vercel serverless handler for Mandelbrot rendering."""
    try:
        # Parse query parameters
        query_string = request.url.split('?', 1)[1] if '?' in request.url else ''
        params = parse_qs(query_string)
        
        # Extract and validate parameters with defaults
        width = int(params.get('width', ['800'])[0])
        height = int(params.get('height', ['600'])[0])
        max_iter = int(params.get('max_iter', ['300'])[0])
        x_center = float(params.get('x_center', ['-0.5'])[0])
        y_center = float(params.get('y_center', ['0.0'])[0])
        scale = float(params.get('scale', ['1.5'])[0])
        
        # Clamp to avoid DoS
        width = max(50, min(2000, width))
        height = max(50, min(2000, height))
        max_iter = max(10, min(20000, max_iter))
        
        # Compute mandelbrot
        div = mandelbrot(width, height, max_iter, x_center, y_center, scale)
        img_arr = color_map(div, max_iter)
        im = Image.fromarray(img_arr, mode='RGB')
        
        # Draw overlay with scale label
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
            
            # Bracket lines
            draw.line([(left, top), (right, top)], fill=(255, 255, 255, 220), width=thickness)
            draw.line([(right, top), (right, bottom)], fill=(255, 255, 255, 220), width=thickness)
            draw.line([(left, bottom), (right, bottom)], fill=(255, 255, 255, 220), width=thickness)
            
            # Scale label
            try:
                from PIL import ImageFont
                font_size = max(12, int(h * 0.04))
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("Arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                label = f"{scale:.2e}"
                text_x = left - (bar_w + 40)
                text_y = top + 6
                draw.text((text_x, text_y), label, font=font, fill=(255, 255, 255, 255))
            except:
                pass
        except:
            pass
        
        # Encode to PNG
        buf = BytesIO()
        im.save(buf, format='PNG')
        png_bytes = buf.getvalue()
        
        # Return response with PNG as base64
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'image/png',
                'Cache-Control': 'public, max-age=3600',
            },
            'body': base64.b64encode(png_bytes).decode('utf-8'),
            'isBase64Encoded': True,
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'text/plain'},
            'body': str(e),
        }
