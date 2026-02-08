#!/usr/bin/env python3
"""Simple zoom UI and headless-friendly generator wrapper."""
import os
import glob
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.widgets as mwidgets
import json
import argparse

import mandelbrot

def generate_and_save(width, height, max_iter, x_center, y_center, scale, out_path):
    """Generate a mandelbrot image and save to out_path."""
    div = mandelbrot.mandelbrot(width, height, max_iter, x_center, y_center, scale)
    img = mandelbrot.color_map(div, max_iter)
    im = Image.fromarray(img, mode="RGB")
    im.save(out_path)


class ZoomApp:
    def __init__(self, init_name, width, height, max_iter, x_center, y_center, scale, prefix="out"):
        self.init_name = init_name
        self.width = width
        self.height = height
        self.max_iter = max_iter
        self.x_center = x_center
        self.y_center = y_center
        self.scale = scale
        self.prefix = prefix

        self.seq = 0
        # committed iteration count (base value)
        self.base_max_iter = self.max_iter
        # cache for incremental mandelbrot computation
        self.cache = None
        # directory to store PNG and JSON frames
        self.out_dir = f"{self.prefix}_frames"
        os.makedirs(self.out_dir, exist_ok=True)

        # Prepare matplotlib figure and axis
        self.fig, self.ax = plt.subplots(figsize=(self.width / 100.0, self.height / 100.0), dpi=100)
        self.ax.set_axis_off()

        # Load initial image (PIL -> numpy array)
        try:
            im = Image.open(self.init_name).convert("RGB")
            if im.size != (self.width, self.height):
                im = im.resize((self.width, self.height))
            arr = np.array(im)
            # show the image; origin='upper' to match image coordinates
            self.im_artist = self.ax.imshow(arr, origin="upper")
        except Exception as e:
            import traceback
            traceback.print_exc()
            # display error text in the axis
            self.im_artist = None
            self.ax.text(0.5, 0.5, f"Error loading image:\n{e}", color="red", ha="center", va="center", transform=self.ax.transAxes)
            # Try to build a computation cache and render from it (faster for iteration increases)
            self.cache = None
            try:
                if hasattr(mandelbrot, "compute_initial_and_cache"):
                    div, cache = mandelbrot.compute_initial_and_cache(self.width, self.height, self.max_iter, self.x_center, self.y_center, self.scale)
                    self.cache = cache
                    arr = mandelbrot.color_map(div, self.max_iter)
                    self.im_artist = self.ax.imshow(arr, origin="upper")
                else:
                    raise AttributeError("no cache API")
            except Exception as e:
                try:
                    import traceback
                    traceback.print_exc()
                except Exception:
                    pass
                # fallback: load initial image file if available
                try:
                    im = Image.open(self.init_name).convert("RGB")
                    if im.size != (self.width, self.height):
                        im = im.resize((self.width, self.height))
                    arr = np.array(im)
                    self.im_artist = self.ax.imshow(arr, origin="upper")
                except Exception as e2:
                    import traceback
                    traceback.print_exc()
                    self.im_artist = None
                    self.ax.text(0.5, 0.5, f"Error loading image:\n{e2}", color="red", ha="center", va="center", transform=self.ax.transAxes)
        self.fig.subplots_adjust(bottom=0.18)
        # display current committed iteration count on the right
        self.iter_text = self.fig.text(0.92, 0.03, f"iters: {self.base_max_iter} (+0%)", ha='right', va='center')

        # Slider for temporary iteration increase (0..1 -> up to +25%)
        try:
            slider_ax = self.fig.add_axes([0.12, 0.05, 0.6, 0.03])
            self.iter_slider = mwidgets.Slider(slider_ax, "Iter+", 0.0, 1.0, valinit=0.0)
            self.iter_slider.on_changed(self._slider_changed)
            # catch release events on the figure to commit the slider value
            self.fig.canvas.mpl_connect('button_release_event', self._slider_released)
        except Exception:
            # if widgets unavailable, continue without slider
            self.iter_slider = None

        # connect mouse click handler
        try:
            self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        except Exception:
            pass

    def _pixel_to_complex(self, px, py):
        x_min = self.x_center - self.scale
        x_max = self.x_center + self.scale
        y_scale = self.scale * self.height / self.width
        y_min = self.y_center - y_scale
        y_max = self.y_center + y_scale

        x = x_min + (x_max - x_min) * px / max(1, (self.width - 1))
        y = y_min + (y_max - y_min) * py / max(1, (self.height - 1))
        return x, y

    def _on_click(self, event):
        # only handle clicks inside the image axes (ignore toolbar/buttons)
        if event.inaxes is not self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        px = int(event.xdata)
        py = int(event.ydata)

        new_x, new_y = self._pixel_to_complex(px, py)
        self.x_center = new_x
        self.y_center = new_y
        # use a 4x zoom per click
        self.scale *= 0.25
        miters = int(self.max_iter * 1.25)  # increase iterations by 25%
        # regenerate image at same center/scale with increased iterations using cache if available
        if self.cache is not None:
            try:
                div = mandelbrot.compute_from_cache(self.cache, miters)
                arr = mandelbrot.color_map(div, miters)
            except Exception:
                div = mandelbrot.mandelbrot(self.width, self.height, miters, self.x_center, self.y_center, self.scale)
                arr = mandelbrot.color_map(div, miters)
        else:
            div = mandelbrot.mandelbrot(self.width, self.height, miters, self.x_center, self.y_center, self.scale)
            arr = mandelbrot.color_map(div, miters)     
        out_name = os.path.join(self.out_dir, f"{self.prefix}_{self.seq:03d}.png")
        generate_and_save(self.width, self.height, self.max_iter, self.x_center, self.y_center, self.scale, out_name)
        # save metadata for this frame so we can interpolate later
        try:
            meta = {
                "x_center": float(self.x_center),
                "y_center": float(self.y_center),
                "scale": float(self.scale),
                "px": int(px),
                "py": int(py),
                "max_iter": int(self.max_iter),
            }
            meta_path = os.path.join(self.out_dir, f"{self.prefix}_{self.seq:03d}.json")
            with open(meta_path, "w") as mf:
                json.dump(meta, mf)
        except Exception:
            pass

        # update displayed image
        try:
            im = Image.open(out_name).convert("RGB")
            if im.size != (self.width, self.height):
                im = im.resize((self.width, self.height))
            arr = np.array(im)
            if self.im_artist is None:
                self.im_artist = self.ax.imshow(arr, origin="upper")
            else:
                self.im_artist.set_data(arr)
            # no persistent change to max_iter here (slider handles temporary increases)
            self.fig.canvas.draw_idle()
        except Exception as e:
            import traceback
            traceback.print_exc()
            # display error text on axis
            self.ax.clear()
            self.ax.text(0.5, 0.5, f"Error generating image:\n{e}", color="red", ha="center", va="center", transform=self.ax.transAxes)
            self.fig.canvas.draw_idle()

        self.seq += 1

    def _slider_changed(self, val):
        """Called while slider moves; temporarily increase iterations up to +25%.

        `val` is in [0,1], where 1.0 corresponds to +25% iterations.
        """
        try:
            # compute temporary iterations
            miters = int(self.base_max_iter * (1.0 + 0.25 * float(val)))
            # regenerate image at same center/scale with increased iterations
            div = mandelbrot.mandelbrot(self.width, self.height, miters, self.x_center, self.y_center, self.scale)
            arr = mandelbrot.color_map(div, miters)
            if self.im_artist is None:
                self.im_artist = self.ax.imshow(arr, origin="upper")
            else:
                self.im_artist.set_data(arr)
            # update temporary iter display on the right (show percent)
            try:
                pct = int(round(100.0 * (miters / float(self.base_max_iter) - 1.0))) if self.base_max_iter else 0
                self.iter_text.set_text(f"iters: {miters} (+{pct}%)")
            except Exception:
                pass
            self.fig.canvas.draw_idle()
        except Exception:
            import traceback
            traceback.print_exc()

    def _slider_released(self, event):
        """Snap slider back to zero on mouse release and re-render with base iterations."""
        try:
            # if slider value is non-zero, commit the temporary increase to base_max_iter
            if getattr(self, 'iter_slider', None) is not None and self.iter_slider.val != 0.0:
                cur_val = float(self.iter_slider.val)
                # compute new committed iterations (up to +25%)
                new_miters = int(self.base_max_iter * (1.0 + 0.25 * cur_val))
                if new_miters != self.base_max_iter:
                    old = self.base_max_iter
                    self.base_max_iter = new_miters
                    self.max_iter = new_miters
                    pct = int(round(100.0 * (self.base_max_iter / float(old) - 1.0))) if old else 0
                else:
                    pct = 0
                # reset slider back to zero (will call _slider_changed with 0.0)
                self.iter_slider.set_val(0.0)
                # update the right-side text to committed value (show percent change from previous)
                try:
                    self.iter_text.set_text(f"iters: {self.base_max_iter} (+{pct}%)")
                except Exception:
                    pass
                # regenerate at committed iterations to ensure exact base rendering
                div = mandelbrot.mandelbrot(self.width, self.height, self.base_max_iter, self.x_center, self.y_center, self.scale)
                arr = mandelbrot.color_map(div, self.base_max_iter)
                if self.im_artist is None:
                    self.im_artist = self.ax.imshow(arr, origin="upper")
                else:
                    self.im_artist.set_data(arr)
                self.fig.canvas.draw_idle()
        except Exception:
            import traceback
            traceback.print_exc()

    def run(self):
        plt.show()
        # After the interactive session ends, create a movie from generated PNGs
        try:
            self.make_movie()
        except Exception:
            import traceback
            traceback.print_exc()

    def make_movie(self, out_name=None, fps=10):
        """Create a GIF movie from all images matching the current prefix.

        Delegates to make_movie_from_dir() with instance parameters.
        """
        return make_movie_from_dir(
            out_dir=self.out_dir,
            prefix=self.prefix,
            out_name=out_name,
            fps=fps,
            width=self.width,
            height=self.height,
            max_iter=self.max_iter,
            steps=15
        )


def make_movie_from_dir(out_dir="zoom_frames", prefix="zoom", out_name=None, fps=10, steps=15, width=800, height=600, max_iter=300):
    """Create a GIF movie from PNGs in `out_dir` with names matching `{prefix}_*.png`.

    Parameters:
      out_dir: directory containing PNG frames and metadata
      prefix: frame filename prefix (e.g., "zoom" for "zoom_000.png")
      out_name: output GIF path (default: <out_dir>/<prefix>.gif)
      fps: frames per second for GIF playback
      steps: interpolation steps between saved frames
      width, height, max_iter: used as fallbacks during interpolation

    Returns the path to the written GIF (out_name).
    """
    if out_name is None:
        out_name = os.path.join(out_dir, f"{prefix}.gif")

    pattern = os.path.join(out_dir, f"{prefix}_*.png")
    files = sorted([p for p in glob.glob(pattern)])
    if not files:
        print(f"[zoom_mode] No images found matching {pattern}; skipping movie creation.")
        return out_name

    print(f"[zoom_mode] Creating movie {out_name} from {len(files)} frames...")

    frames = []

    def load_meta(png_path):
        base = os.path.splitext(png_path)[0]
        meta_path = f"{base}.json"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as mf:
                    return json.load(mf)
            except Exception:
                return None
        return None

    metas = [load_meta(p) for p in files]
    initial_scale = None
    if metas and metas[0] and "scale" in metas[0]:
        initial_scale = float(metas[0]["scale"])

    def overlay_scale_bar(pil_img, scale_val):
        try:
            draw = ImageDraw.Draw(pil_img, 'RGBA')
            w, h = pil_img.size
            bar_w = max(12, int(w * 0.045))
            padding = max(8, int(w * 0.02))

            # bracket coordinates (']' shape)
            left = w - bar_w - padding
            right = w - padding
            top = padding
            bottom = h - padding
            thickness = max(2, int(bar_w * 0.25))

            # draw bracket outline
            draw.line([(left, top), (right, top)], fill=(255, 255, 255, 230), width=thickness)
            draw.line([(right, top), (right, bottom)], fill=(255, 255, 255, 230), width=thickness)
            draw.line([(left, bottom), (right, bottom)], fill=(255, 255, 255, 230), width=thickness)

            label = None
            if scale_val is not None:
                try:
                    label = f"{float(scale_val):.2e}"
                except Exception:
                    label = None

            font_size = max(12, int(h * 0.04))
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", font_size)
            except Exception:
                try:
                    font = ImageFont.truetype("Arial.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()

            if label:
                text_x = left - (bar_w + 60)
                text_y = top + 6
                try:
                    draw.multiline_text((text_x, text_y), label, font=font, fill=(255, 255, 255, 255), align="right", stroke_width=2, stroke_fill=(0, 0, 0, 200))
                except TypeError:
                    draw.multiline_text((text_x + 1, text_y + 1), label, font=font, fill=(0, 0, 0, 200), align="right")
                    draw.multiline_text((text_x, text_y), label, font=font, fill=(255, 255, 255, 255), align="right")
        except Exception:
            pass

    # infer base width/height from first image if available
    try:
        with Image.open(files[0]) as _im:
            base_w, base_h = _.size
    except Exception:
        base_w, base_h = width, height

    for idx in range(len(files)):
        p = files[idx]
        try:
            im_next = Image.open(p).convert("RGBA")
        except Exception:
            import traceback
            traceback.print_exc()
            continue

        meta = metas[idx] if idx < len(metas) else None
        if meta and "scale" in meta and initial_scale is not None:
            sc = float(meta.get("scale", initial_scale))
            overlay_scale_bar(im_next, sc)

        frames.append(im_next)

        # interpolate to next frame if metadata available
        if idx + 1 < len(files):
            meta_a = load_meta(files[idx])
            meta_b = load_meta(files[idx + 1])
            if meta_a and meta_b:
                for s in range(1, steps + 1):
                    t = s / float(steps + 1)
                    cx = (1 - t) * meta_a.get("x_center", 0.0) + t * meta_b.get("x_center", 0.0)
                    cy = (1 - t) * meta_a.get("y_center", 0.0) + t * meta_b.get("y_center", 0.0)
                    sc = (1 - t) * meta_a.get("scale", 1.0) + t * meta_b.get("scale", 1.0)
                    miters = int((1 - t) * meta_a.get("max_iter", max_iter) + t * meta_b.get("max_iter", max_iter))
                    try:
                        w = base_w or int(meta_a.get("width", width))
                        h = base_h or int(meta_a.get("height", height))
                        div = mandelbrot.mandelbrot(w, h, miters, cx, cy, sc)
                        arr = mandelbrot.color_map(div, miters)
                        im_interp = Image.fromarray(arr, mode="RGB").convert("RGBA")
                        if initial_scale is not None:
                            overlay_scale_bar(im_interp, sc)
                        frames.append(im_interp)
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        break

    if not frames:
        print("[zoom_mode] No valid frames to write; aborting movie creation.")
        return out_name

    try:
        duration = int(1000 / max(1, fps))
        frames[0].save(out_name, save_all=True, append_images=frames[1:], duration=duration, loop=0, disposal=2)
        print(f"[zoom_mode] Movie saved to {out_name}")
    except Exception:
        import traceback
        traceback.print_exc()
    return out_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zoomable Mandelbrot viewer and GIF exporter")
    parser.add_argument("--width", type=int, default=300)
    parser.add_argument("--height", type=int, default=200)
    parser.add_argument("--max-iter", type=int, default=100)
    parser.add_argument("--x-center", type=float, default=-0.5)
    parser.add_argument("--y-center", type=float, default=0.0)
    parser.add_argument("--scale", type=float, default=1.5)
    parser.add_argument("--init", type=str, default="initial.png", help="initial image filename (will be generated if missing)")
    parser.add_argument("--prefix", type=str, default="zoom", help="output prefix for saved frames and movie")
    args = parser.parse_args()

    init = args.init
    width = args.width
    height = args.height
    max_iter = args.max_iter
    x_center = args.x_center
    y_center = args.y_center
    scale = args.scale
    prefix = args.prefix

    # prepare output directory and remove any existing PNG/JSON frames for this prefix
    out_dir = f"{prefix}_frames"
    os.makedirs(out_dir, exist_ok=True)
    for pattern in (os.path.join(out_dir, "*.png"), os.path.join(out_dir, "*.json")):
        for p in glob.glob(pattern):
            try:
                os.remove(p)
            except Exception:
                pass
    # remove existing gif in the frames dir for this prefix
    gif_path = os.path.join(out_dir, f"{prefix}.gif")
    if os.path.exists(gif_path):
        try:
            os.remove(gif_path)
        except Exception:
            pass

    if not os.path.exists(init):
        generate_and_save(width, height, max_iter, x_center, y_center, scale, init)

    app = ZoomApp(init, width, height, max_iter, x_center, y_center, scale, prefix)
    app.run()