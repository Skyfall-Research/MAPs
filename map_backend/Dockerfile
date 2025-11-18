# Dockerfile for MAP Backend Server
# NOTE: This Dockerfile expects to be built from the parent directory (map/)
# Build command: docker build -f map_backend/Dockerfile -t map_backend .

FROM node:20

# Set working directory
WORKDIR /app

# Copy package files from parent directory
COPY package*.json ./

# Install dependencies
# Use npm install for better compatibility
RUN npm install --omit=dev

# Copy shared configuration and assets (needed by backend)
COPY shared ./shared

# Copy backend source code
COPY map_backend ./map_backend

# Set environment to production
ENV NODE_ENV=production

# Expose the port the backend runs on
EXPOSE 3000

# Start the backend server
# Use --vis flag to enable visualization updates
CMD ["node", "map_backend/server.js", "--vis"]
