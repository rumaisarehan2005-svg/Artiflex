# Use official python:3.10-slim
FROM python:3.10-slim

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV NODE_ENV=production

# Install curl, Node.js and other system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create user with UID 1000 to match Hugging Face Space security guidelines
RUN useradd -m -u 1000 user

# Set work directory
WORKDIR /app

# Copy dependency manifests first for build caching
COPY --chown=user:user package.json package-lock.json ./
COPY --chown=user:user backend/requirements.txt ./backend/

# Install python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install node dependencies
RUN npm ci

# Copy the rest of the application
COPY --chown=user:user . .

# Build the Next.js application
RUN npm run build

# Switch to non-root user
USER user

# Expose Hugging Face Space default port
EXPOSE 7860

# Give execute permissions to start script
RUN chmod +x start.sh

# Run startup script
CMD ["./start.sh"]
