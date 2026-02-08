Vercel deployment instructions

- Requirements
  - Install the Vercel CLI: `npm i -g vercel` or visit https://vercel.com/docs
  - Ensure you have a Vercel account and are logged in: `vercel login`

- What this repo provides for Vercel
  - Serverless functions live under `api/` (e.g. `api/mandelbrot.py`).
  - Python dependencies for functions are in `api/requirements.txt`.
  - Static site files are under `public/` and the root `index.html`.
  - `vercel.json` configures the Python builder for `api/*.py`.
  - `runtime.txt` requests Python 3.11.

- Quick deploy (production)

```bash
vercel --prod
```

- Local development (previewing serverless functions and static files)

```bash
vercel dev
# open http://localhost:3000
```

- Notes
  - The serverless handler in `api/mandelbrot.py` implements `handler(request)` and returns a Vercel-compatible response (base64 PNG in `body` with `isBase64Encoded`).
  - If you need a single endpoint name, Vercel exposes `api/mandelbrot.py` at `/api/mandelbrot` by default.
  - Keep an eye on `api/requirements.txt` — heavy packages may increase cold-start time.

*** End Draft
