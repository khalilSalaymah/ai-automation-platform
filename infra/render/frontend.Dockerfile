# Dockerfile for Render.com frontend deployment
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY packages/ui/package.json packages/ui/package-lock.json* ./packages/ui/

# Install dependencies
WORKDIR /app/packages/ui
RUN npm ci

# Copy source code
COPY packages/ui .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/packages/ui/dist /usr/share/nginx/html

# Copy nginx configuration
COPY infra/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
