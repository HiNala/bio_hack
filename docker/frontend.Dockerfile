# ScienceRAG Frontend Dockerfile
# Multi-stage Next.js build with optimized caching

FROM node:20-alpine AS base

# Metadata
LABEL maintainer="ScienceRAG Team"
LABEL description="Next.js frontend for ScienceRAG"

# Install system dependencies
RUN apk add --no-cache libc6-compat curl

# Set environment
ENV NEXT_TELEMETRY_DISABLED=1

# Dependencies stage (production only)
FROM base AS deps
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install production dependencies only
RUN \
  if [ -f package-lock.json ]; then npm ci --only=production; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Development dependencies stage
FROM base AS deps-dev
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install ALL dependencies (including devDependencies like typescript)
RUN \
  if [ -f package-lock.json ]; then npm ci; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Development stage
FROM base AS dev
WORKDIR /app

# Create non-root user BEFORE copying files
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy dependencies with correct ownership
COPY --from=deps-dev --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --chown=nextjs:nodejs frontend/ .

# Set development environment
ENV NODE_ENV=development

USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

EXPOSE 3000

CMD ["npm", "run", "dev"]

# Build stage
FROM base AS builder
WORKDIR /app

# Copy ALL dependencies (need devDependencies like typescript for build)
COPY --from=deps-dev /app/node_modules ./node_modules
COPY frontend/ .

# Set production environment for build
ENV NODE_ENV=production

# Build application
RUN npm run build

# Production stage
FROM base AS production
WORKDIR /app

# Set production environment
ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
