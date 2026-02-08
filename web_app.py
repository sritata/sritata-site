#!/usr/bin/env python3
"""Minimal Flask web app to run the mandelbrot generator interactively."""
import os
import time
from io import BytesIO

from flask import Flask, request, send_file, render_template, url_for
from PIL import Image, ImageDraw, ImageFont

import mandelbrot

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, "templates"),
    static_folder=os.path.join(ROOT_DIR, "static"),
    static_url_path="/static",
)


def _parse_params(args):
    try:
        width = int(args.get("width", 800))
        height = int(args.get("height", 600))
        max_iter = int(args.get("max_iter", 300))
        x_center = float(args.get("x_center", -0.5))
        y_center = float(args.get("y_center", 0.0))
        scale = float(args.get("scale", 1.5))
    except Exception:
        return None

    width = max(50, min(2000, width))
    height = max(50, min(2000, height))
    max_iter = max(10, min(20000, max_iter))
    return width, height, max_iter, x_center, y_center, scale


def _render_mandelbrot_png_bytes(width, height, max_iter, x_center, y_center, scale) -> bytes:
    div = mandelbrot.mandelbrot(width, height, max_iter, x_center, y_center, scale)
    arr = mandelbrot.color_map(div, max_iter)
    im = Image.fromarray(arr, mode="RGB")

    # Optional scale bar overlay (your code)
    try:
        draw = ImageDraw.Draw(im, "RGBA")
        w, h = im.size
        bar_w = max(12, int(w * 0.045))
        padding = max(8, int(w * 0.02))
        left = w - bar_w - padding
        right = w - padding
        top = padding
        bottom = h - padding
        thickness = max(2, int(bar_w * 0.25))

        draw.line([(left, top), (right, top)], fill=(255, 255, 255, 220), width=thickness)
        draw.line([(right, top), (right, bottom)], fill=(255, 255, 255, 220), width=thickness)
        draw.line([(left, bottom), (right, bottom)], fill=(255, 255, 255, 220), width=thickness)

        try:
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
            draw.text((text_x, text_y), label, font=font, fill=(255, 255, 255, 255))
        except Exception:
            pass
    except Exception:
        pass

    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _render_page_for_params(width, height, max_iter, x_center, y_center, scale):
    # Cache-bust image URL so repeats re-fetch
    img_url = url_for(
        "render_image_png",
        width=width,
        height=height,
        max_iter=max_iter,
        x_center=x_center,
        y_center=y_center,
        scale=scale,
        _=str(int(time.time() * 1000)),
    )

    # Optional overlay file: static/overlay.png
    overlay_path = os.path.join(app.static_folder, "overlay.png")
    overlay_url = url_for("static", filename="overlay.png") if os.path.exists(overlay_path) else None

    return render_template(
        "mandelbrot.html",
        width=width,
        height=height,
        max_iter=max_iter,
        x_center=x_center,
        y_center=y_center,
        scale=scale,
        img_url=img_url,
        overlay_url=overlay_url,
        page_endpoint=url_for("render_page"),
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/mandelbrot")
def mandelbrot_page():
    parsed = _parse_params(request.args)
    if parsed is None:
        parsed = (800, 600, 300, -0.5, 0.0, 1.5)
    width, height, max_iter, x_center, y_center, scale = parsed
    return _render_page_for_params(width, height, max_iter, x_center, y_center, scale)


@app.get("/render")
def render_page():
    parsed = _parse_params(request.args)
    if parsed is None:
        return "Bad parameters", 400
    width, height, max_iter, x_center, y_center, scale = parsed
    return _render_page_for_params(width, height, max_iter, x_center, y_center, scale)


@app.get("/render.png")
def render_image_png():
    parsed = _parse_params(request.args)
    if parsed is None:
        return "Bad parameters", 400
    width, height, max_iter, x_center, y_center, scale = parsed

    png_bytes = _render_mandelbrot_png_bytes(width, height, max_iter, x_center, y_center, scale)
    return send_file(BytesIO(png_bytes), mimetype="image/png")


if __name__ == "__main__":
    # Local dev: avoid threaded mode if Numba parallelism complains about concurrency
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=False)
