# ── Hugging Face Spaces – Streamlit app ───────────────────────────────────────
# HF Spaces runs as user 1000; set HOME explicitly to avoid permission issues.

FROM python:3.11-slim

# HF requirement: expose port 7860
ENV PORT=7860 \
    HOME=/home/user \
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create non-root user expected by HF Spaces
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY --chown=user . .

USER 1000

EXPOSE 7860

CMD ["streamlit", "run", "app.py"]
