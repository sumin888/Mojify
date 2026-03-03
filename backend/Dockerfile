FROM python:3.11-slim

WORKDIR /app

# Install Litestream (SQLite replication to GCS for data persistence on Cloud Run)
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    wget -qO /tmp/litestream.tar.gz \
      https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.tar.gz && \
    tar -xzf /tmp/litestream.tar.gz -C /usr/local/bin litestream && \
    rm /tmp/litestream.tar.gz && \
    apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

RUN chmod +x /app/start.sh

# Cloud Run sets PORT env var
ENV PORT=8080
EXPOSE 8080

CMD ["/app/start.sh"]
