# Build from repository root:
#   docker build -f slideshow_hub/Dockerfile -t slideshow-hub .
FROM python:3.12-slim

WORKDIR /app

COPY slideshow_hub/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY slideshow_hub ./slideshow_hub

ENV PYTHONUNBUFFERED=1
EXPOSE 8090

CMD ["uvicorn", "slideshow_hub.main:app", "--host", "0.0.0.0", "--port", "8090"]
