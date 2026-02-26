FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM deps AS builder
WORKDIR /app
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
RUN printf '%s\n' '/** @type {import("next").NextConfig} */' 'const nextConfig = {};' 'export default nextConfig;' > next.config.mjs

EXPOSE 3000
CMD ["npm", "run", "start"]
