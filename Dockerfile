# Unified Mojify: backend + frontend in one image, single Cloud Run URL
# Build from project root: docker build -f Dockerfile .
# Layer order: deps first (cached when only source changes), source last

# ── Stage 1: Litestream binary ────────────────────────────────────────────────
FROM litestream/litestream:latest AS litestream

# ── Stage 2: Build frontend ───────────────────────────────────────────────────
FROM node:20-alpine AS frontend
WORKDIR /app
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# Dependencies first — layer cached when only source changes, not package.json
COPY frontend/package*.json ./
RUN npm ci --prefer-offline --no-audit --no-fund

COPY frontend/ .
RUN npm run build

# ── Stage 3: Backend with frontend baked in ───────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Litestream binary from dedicated stage (no wget/tar overhead in this layer)
COPY --from=litestream /usr/local/bin/litestream /usr/local/bin/litestream

# Python dependencies — cached when requirements.txt unchanged
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source
COPY backend/ .

# Frontend build output
COPY --from=frontend /app/dist ./frontend_dist

RUN chmod +x /app/start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["/app/start.sh"]
