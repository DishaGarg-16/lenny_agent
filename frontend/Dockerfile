FROM node:20-alpine

WORKDIR /app

# Copy dependency specifications and install
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code
COPY index.html vite.config.js ./
COPY src/ ./src/

EXPOSE 3000

# Start Vite dev server accessible externally
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
