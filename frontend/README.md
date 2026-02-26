# Frontend Dashboard

Frontend for the Multimodal Drone Detection project.

## Tech Stack
- Next.js 16 (App Router)
- React 19
- Tailwind CSS v4
- shadcn/ui
- Lucide Icons

## Local Development
```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

## Available Routes
- `/live-feed`
- `/incidents`
- `/settings`

## Current Scope (Sprint 1 Static UI)
- Dashboard navigation shell
- Live Feed static layout and metrics
- Incidents static table, filters, and pagination
- Settings static form controls

## Theme
- Top-bar toggle switches between Light and Dark mode.
- Theme preference is stored in browser local storage.

## Build

### Local Production Run (without Docker)
```bash
cd frontend
npm run build
npm run start
```

### Docker Deployment
From repository root:
```bash
docker build -t drone-detection-frontend -f frontend/Dockerfile frontend
docker run --rm -p 3000:3000 drone-detection-frontend
```
