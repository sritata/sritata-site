# Archive Directory

This directory contains files that are not needed for the Vercel web deployment but may be useful for local development or reference.

## Files

- **`mandelbrot.py`**: Local Python script with numba optimizations for generating Mandelbrot images. Not needed for web deployment (web uses `api/mandelbrot.py` instead).

- **`web_app.py`**: Flask web application for local development. Not used by Vercel (Vercel uses its own serverless platform).

- **`zoom_mode.py`**: Interactive matplotlib tool for exploring the Mandelbrot set with zoom functionality. Not needed for web deployment.

- **`requirements.txt`**: Python dependencies for local scripts. Not used by Vercel (web uses `api/requirements.txt` instead).

- **`runtime.txt`**: Python runtime specification. Not used by Vercel.

## Web Deployment

The website at sritata.com uses only:
- `index.html` - Home page
- `public/` - Static assets
- `api/mandelbrot.py` - Serverless function for rendering
- `api/requirements.txt` - Dependencies for serverless function
- `vercel.json` - Deployment configuration
