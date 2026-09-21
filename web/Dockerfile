# Deps installs packages and builder compiles Next.js; runner copies only runtime artifacts, leaving the build toolchain behind.
FROM node:22-alpine AS deps

RUN corepack enable && corepack prepare pnpm@10.25.0 --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder

RUN corepack enable && corepack prepare pnpm@10.25.0 --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
# NEXT_PUBLIC_* is inlined into the client bundle by `next build`, so it must be a build
# arg. Supplying it only at runtime via env_file would leave the compiled JavaScript
# pointing at whatever value was set when the image was made.
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN pnpm build

FROM node:22-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --from=builder --chown=node:node /app/public ./public
USER node
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=6 \
    CMD wget --spider -q http://127.0.0.1:3000/ || exit 1
CMD ["node", "server.js"]
