# ── Stage 1: Системные библиотеки, шрифты, локали ──
FROM python:3.12-slim AS system-deps

RUN apt-get update && apt-get install -y --no-install-recommends \
        locales tzdata ca-certificates \
        fonts-noto fonts-dejavu-core fonts-liberation \
        libgtk-3-0 libasound2 libx11-xcb1 libxcomposite1 libxrandr2 \
        libxss1 libatk-bridge2.0-0 \
        libgl1 libegl1 libdrm2 libgbm1 libxshmfence1 libxcursor1 libxi6 \
        libnss3 libdbus-glib-1-2 \
        dbus-x11 xdg-utils xvfb libgl1-mesa-dri \
    && locale-gen ru_RU.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=ru_RU.UTF-8 LC_ALL=ru_RU.UTF-8 TZ=Europe/Moscow


# ── Stage 2: Python-зависимости + playwright install-deps ──
FROM system-deps AS python-deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install-deps firefox \
    && rm -rf /var/lib/apt/lists/*


# ── Stage 3: Загрузка браузера Camoufox ──
FROM python-deps AS browser

RUN camoufox fetch


# ── Stage 4: Runtime (наследует всё от browser) ──
FROM browser AS runtime

RUN useradd -m -s /bin/bash camouser \
    && mkdir -p /home/camouser/.cache \
    && cp -r /root/.cache/camoufox /home/camouser/.cache/camoufox \
    && chown -R camouser:camouser /home/camouser

ENV HOME=/home/camouser
ENV PYTHONPATH=/app

WORKDIR /app
COPY --chown=camouser:camouser src/ src/

USER camouser
CMD ["python", "src/main.py"]
