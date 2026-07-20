FROM python:3.11-slim AS pydeps

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pipeline/env_generator/requirements.txt ./pipeline/env_generator/requirements.txt
RUN python -m pip install --no-cache-dir --no-compile --target=/opt/python -r pipeline/env_generator/requirements.txt

FROM node:20-bookworm-slim AS nodebase

WORKDIR /app

COPY backend/package*.json ./backend/
RUN cd backend && npm ci --omit=dev

FROM node:20-bookworm-slim AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV PYTHONPATH=/opt/python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg
ENV PYTHON_EXECUTABLE=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --from=pydeps /opt/python /opt/python

COPY --from=nodebase /app/backend/node_modules ./backend/node_modules
COPY backend/package*.json ./backend/
COPY backend/server.js ./backend/server.js
COPY backend/src ./backend/src
COPY pipeline ./pipeline

USER appuser

WORKDIR /app/backend

EXPOSE 5000

CMD ["node", "server.js"]
