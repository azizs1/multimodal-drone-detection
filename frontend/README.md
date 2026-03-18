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
cp .env.example .env.local
npm run dev
```

Open: `http://localhost:3000`

### Environment Variables
- `NEXT_PUBLIC_API_BASE_URL` (default fallback: `http://localhost:8000`)
- Example:
  - File: `.env.local`
  - Value: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

## Available Routes
- `/live-feed`
- `/incidents`
- `/settings`

## Current Scope
- Dashboard navigation shell
- Live Feed HLS playback for RGB/Thermal streams
- Live Feed stream metadata + retry states
- Incidents static table, filters, and pagination
- Settings static form controls

## Live Feed Local Run Flow
### Prerequisites
From repository root, run backend/media stack:
```bash
docker compose -f docker-compose-dev.yml up --build
```

Expected services:
- Backend API: `http://localhost:8000/streams`
- HLS visual: `http://localhost:8888/visual/index.m3u8`
- HLS thermal: `http://localhost:8888/thermal/index.m3u8`

### Validation Checklist
1. Open `http://localhost:3000/live-feed`.
2. Confirm both RGB/Thermal panels are playing.
3. Stop one simulator and refresh:
   ```bash
   docker stop gst-visual-simulator
   ```
4. Confirm interrupted state appears with `Retry`.
5. Start simulator and click `Retry`:
   ```bash
   docker start gst-visual-simulator
   ```
6. (Optional) Stop backend, refresh, and verify metadata error banner appears.

## Quality Checks
```bash
cd frontend
npm run lint
npm run test
```

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
docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://host.docker.internal:8000 \
  -t drone-detection-frontend \
  -f frontend/Dockerfile frontend
docker run --rm -p 3000:3000 drone-detection-frontend
```

Notes:
- `NEXT_PUBLIC_API_BASE_URL` is injected at build time for the frontend bundle.
- For non-local environments, replace `http://host.docker.internal:8000` with your backend URL.
