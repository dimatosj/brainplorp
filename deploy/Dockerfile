FROM rust:latest as builder

# Install build dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone and build TaskChampion sync server
WORKDIR /build
RUN git clone https://github.com/GothenburgBitFactory/taskchampion-sync-server.git
WORKDIR /build/taskchampion-sync-server
RUN rm Cargo.lock && cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Copy binary from builder
COPY --from=builder /build/taskchampion-sync-server/target/release/taskchampion-sync-server /usr/local/bin/

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Run server
CMD ["taskchampion-sync-server", "--listen", "0.0.0.0:8080", "--data-dir", "/data"]
