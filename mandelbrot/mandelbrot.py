#!/usr/bin/env python3
import argparse
import numpy as np
try:
    from numba import njit, prange
except Exception:
    # numba not available — provide passthroughs so code can run in pure Python
    def njit(*dargs, **dkwargs):
        # support usage as @njit or @njit(...)
        if dargs and callable(dargs[0]) and not dkwargs:
            return dargs[0]
        def _decorator(func):
            return func
        return _decorator

    def prange(x):
        return range(x)
from PIL import Image


@njit(parallel=True, fastmath=True)
def mandelbrot(width, height, max_iter, x_center, y_center, scale):
    div_time = np.empty((height, width), dtype=np.int32)

    x_min = x_center - scale
    x_max = x_center + scale
    y_scale = scale * height / width
    y_min = y_center - y_scale
    y_max = y_center + y_scale

    for j in prange(height):
        y0 = y_min + (y_max - y_min) * j / (height - 1)

        for i in range(width):
            x0 = x_min + (x_max - x_min) * i / (width - 1)

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


# --- Iterative/resumable implementation helpers ---
@njit(parallel=True, fastmath=True)
def _mandelbrot_iter(zx, zy, iters, x0, y0, div_time, start_iter, max_iter):
    h, w = zx.shape
    for iteration in range(start_iter, max_iter):
        for j in prange(h):
            for i in range(w):
                if div_time[j, i] == 0:
                    x = zx[j, i]
                    y = zy[j, i]
                    xtemp = x * x - y * y + x0[j, i]
                    y = 2.0 * x * y + y0[j, i]
                    x = xtemp
                    zx[j, i] = x
                    zy[j, i] = y
                    iters[j, i] += 1
                    if x * x + y * y > 4.0:
                        div_time[j, i] = iters[j, i]

    # finalize any points that never escaped by assigning the iterations reached
    for j in prange(h):
        for i in range(w):
            if div_time[j, i] == 0:
                div_time[j, i] = iters[j, i]


def _build_grid(width, height, x_center, y_center, scale):
    x_min = x_center - scale
    x_max = x_center + scale
    y_scale = scale * height / width
    y_min = y_center - y_scale
    y_max = y_center + y_scale

    x = np.empty((height, width), dtype=np.float64)
    y = np.empty((height, width), dtype=np.float64)
    for j in range(height):
        y0 = y_min + (y_max - y_min) * j / (height - 1)
        for i in range(width):
            x0 = x_min + (x_max - x_min) * i / (width - 1)
            x[j, i] = x0
            y[j, i] = y0
    return x, y


def create_cache(width, height, x_center, y_center, scale):
    """Create an empty cache for iterative Mandelbrot computation.

    Returns a dict with arrays: zx, zy, iters, x0, y0, div_time, current_iter
    """
    x0, y0 = _build_grid(width, height, x_center, y_center, scale)
    zx = np.zeros((height, width), dtype=np.float64)
    zy = np.zeros((height, width), dtype=np.float64)
    iters = np.zeros((height, width), dtype=np.int32)
    div_time = np.zeros((height, width), dtype=np.int32)
    return {
        "zx": zx,
        "zy": zy,
        "iters": iters,
        "x0": x0,
        "y0": y0,
        "div_time": div_time,
        "current_iter": 0,
    }


def compute_from_cache(cache, target_iter):
    """Continue computation using values in `cache` up to `target_iter`.

    Modifies the cache in-place and returns the updated `div_time` array.
    """
    start = int(cache.get("current_iter", 0))
    if target_iter <= start:
        return cache["div_time"]

    _mandelbrot_iter(cache["zx"], cache["zy"], cache["iters"], cache["x0"], cache["y0"], cache["div_time"], start, int(target_iter))
    cache["current_iter"] = int(target_iter)
    return cache["div_time"]


def compute_initial_and_cache(width, height, max_iter, x_center, y_center, scale):
    """Create a cache and compute the Mandelbrot set up to `max_iter`.

    Returns (div_time, cache)
    """
    cache = create_cache(width, height, x_center, y_center, scale)
    compute_from_cache(cache, max_iter)
    return cache["div_time"], cache


def color_map(div_time, max_iter):
    norm = div_time.astype(float) / max_iter
    norm = np.sqrt(norm)
    r = np.uint8(255 * np.clip(3 * (1 - norm), 0, 1))
    g = np.uint8(255 * np.clip(3 * np.abs(norm - 0.5), 0, 1))
    b = np.uint8(255 * np.clip(3 * norm, 0, 1))
    rgb = np.dstack((r, g, b))
    return rgb    


def main():
    parser = argparse.ArgumentParser(description="Generate a Mandelbrot set PNG")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)
    parser.add_argument("--max-iter", type=int, default=300)
    parser.add_argument("--x-center", type=float, default=-0.5)
    parser.add_argument("--y-center", type=float, default=0.0)
    parser.add_argument("--scale", type=float, default=1.5)
    parser.add_argument("--output", type=str, default="mandelbrot.png")
    args = parser.parse_args()
    div = mandelbrot(args.width, args.height, args.max_iter, args.x_center, args.y_center, args.scale)
    img = color_map(div, args.max_iter)
    im = Image.fromarray(img, mode="RGB")
    im.save(args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()