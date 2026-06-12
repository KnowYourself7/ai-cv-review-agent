FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY cv_review_agent ./cv_review_agent
COPY app.py README.md ./
COPY .streamlit ./.streamlit

RUN uv sync --frozen --no-dev

EXPOSE 8501

CMD ["sh", "-c", "uv run streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-8501}"]
