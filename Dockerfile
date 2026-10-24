# Bağımlılıklar ayrı aşamada derleniyor; son imajda derleyici ve pip önbelleği yok.
FROM python:3.12-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
# MP3 dönüşümü ve MP4 birleştirme için ffmpeg şart
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /install /usr/local

RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY app ./app
COPY static ./static
COPY main.py .
RUN mkdir downloads && chown app:app downloads
USER app

ENV CONVERTER_HOST=0.0.0.0 \
    CONVERTER_PORT=8000 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4)"
CMD ["python", "main.py"]
