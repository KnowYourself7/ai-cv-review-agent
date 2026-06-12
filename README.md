# AI CV Review Agent

Local web app for uploading PDF/DOCX resumes, maintaining 1 to 3 job templates, and ranking candidates by job fit.

## Setup

Create a fresh OpenAI API key and save it locally:

```bash
printf 'OPENAI_API_KEY=your_new_key_here\n' > .env.local
```

Do not commit `.env.local`.

Install dependencies and run tests:

```bash
uv sync --extra dev
uv run pytest
```

Run the app:

```bash
uv run streamlit run app.py
```

## Free temporary sharing with Cloudflare Tunnel

Cloudflare Tunnel can expose the local Streamlit app through a public HTTPS URL without changing the app code.

This option is best for quick internal review:

- The Mac running the app must stay on.
- The Streamlit process and `cloudflared` process must keep running.
- The generated `trycloudflare.com` URL is temporary and changes when the tunnel restarts.
- Candidate data, scores, and original resume files stay in the local SQLite database.

Start the app with an access password:

```bash
APP_PASSWORD='choose_a_strong_password' uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8510
```

In another terminal, start the tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8510
```

Open the printed `https://...trycloudflare.com` URL and unlock the app with `APP_PASSWORD`.

## Private deployment on Render

This app stores candidate details, review scores, and original resume files in SQLite. Use a private deployment with a persistent disk.

Render is a better fit when the app needs a stable URL and should keep running after your local computer is shut down. Persistent disks on Render require a paid service.

Required environment variables:

```text
OPENAI_API_KEY=<set in Render dashboard>
APP_PASSWORD=<set a strong admin password>
CV_REVIEW_DB_PATH=/var/data/cv_review.sqlite3
```

Render setup:

1. Push this repository to GitHub.
2. Create a Render Blueprint from `render.yaml`, or create a Docker Web Service manually.
3. Attach a persistent disk mounted at `/var/data`.
4. Set `OPENAI_API_KEY` and `APP_PASSWORD` in Render environment variables.
5. Confirm `CV_REVIEW_DB_PATH` is `/var/data/cv_review.sqlite3`.
6. Deploy, open the Render URL, and unlock the app with `APP_PASSWORD`.

The Docker startup command is:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port "$PORT"
```

Do not commit `.env.local`, `data/`, downloaded resumes, or database files.

## Notes

- v1 supports text-based PDF and DOCX files. Scanned PDFs/OCR are out of scope.
- Screening output is decision support only. A human reviewer must confirm final hiring decisions.
- Do not score candidates using protected or job-irrelevant traits.
