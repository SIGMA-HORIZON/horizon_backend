# Base stage for dependencies
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install

# Development stage (pour hot-reload)
FROM base AS development
COPY . .
EXPOSE 3006
CMD ["npm", "run", "dev"]

# Build stage (pour prod)
FROM base AS builder
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "start"]