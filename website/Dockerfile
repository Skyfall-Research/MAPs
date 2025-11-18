# Multi-stage build for SvelteKit website
# NOTE: This Dockerfile expects to be built from the parent directory (map/)
# Build command: docker build -f website/Dockerfile -t map-website .
#
# Stage 1: Build the application
FROM node:20 AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY website/package*.json ./

# Install all dependencies (including devDependencies for build)
# Use npm install instead of npm ci since package-lock.json may not be available
RUN npm install

# Copy website source code (excluding static directory which only contains symlinks)
COPY website/package*.json website/svelte.config.js website/vite.config.ts website/tailwind.config.js website/tsconfig.json website/components.json ./
COPY website/src ./src

# Copy shared assets to static directory
# This replaces the symlink approach used in local development
# .dockerignore handles exclusions (.DS_Store, etc.)
RUN mkdir -p ./static
COPY shared/ ./static/

# Generate .svelte-kit directory and configuration files
# This is required before building
RUN npm run prepare

# Build the SvelteKit application
# This creates the production server in ./build
RUN npm run build

# Stage 2: Production runtime
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files for production dependencies
COPY website/package*.json ./

# Install only production dependencies
RUN npm install --omit=dev

# Copy built application from builder stage
COPY --from=builder /app/build ./build
COPY --from=builder /app/static ./static

# Set environment to production
ENV NODE_ENV=production

# Expose the port the app runs on
EXPOSE 3001

# Start the application
CMD ["node", "build"]
