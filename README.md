# Social Empowerment Platform

A real-time emergency and incident detection, video stream management, and responder empowerment system.

---

## 👥 Team Module Ownership

| Member | Focus Area | Directory Scope |
|---|---|---|
| **Member 1 [M1]** | Camera, Stream Gateway & Nginx | `services/video-gateway/`, `apps/web/src/features/camera/`, `services/api/app/devices/`, `services/api/app/streams/`, `infrastructure/nginx/` |
| **Member 2 [M2]** | AI & Computer Vision Worker | `services/ai-worker/` (Ingestion, Preprocessing, Detectors: Fire/Smoke/Accident, Tracking, Events), `services/api/app/ai_detections/`, `docs/ai-models/` |
| **Member 3 [M3]** | Backend Core, Workers, DB & Infra | `services/api/` (Auth, Users, Incidents, Assignments, Notifications, Analytics, WebSocket, Database), `services/notification-worker/`, `infrastructure/docker/`, `infrastructure/monitoring/`, `docker-compose.yml`, `.env.example` |
| **Member 4 [M4]** | Web Frontend, Shared Packages & Docs | `apps/web/` (App, Auth, Handler, Admin, Components), `packages/` (`shared-types`, `api-client`, `ui`), `docs/` (`architecture`, `api`, `database`) |

---

## 📁 Project Structure

```
social-empowerment-platform/
│
├── apps/
│   └── web/                                      # React + Vite + TypeScript [M4]
│       └── src/
│           ├── app/                              # [M4]
│           ├── features/
│           │   ├── auth/                         # [M4]
│           │   ├── camera/                       # [M1]
│           │   ├── handler/                      # [M4]
│           │   └── admin/                        # [M4]
│           ├── components/                       # [M4]
│           └── main.tsx                          # [M4]
│
├── services/
│   ├── api/                                     # FastAPI backend [M3]
│   │   └── app/
│   │       ├── auth/                             # [M3]
│   │       ├── users/                            # [M3]
│   │       ├── devices/                          # [M1]
│   │       ├── streams/                          # [M1]
│   │       ├── incidents/                        # [M3]
│   │       ├── ai_detections/                    # [M2]
│   │       ├── assignments/                      # [M3]
│   │       ├── notifications/                    # [M3]
│   │       ├── analytics/                        # [M3]
│   │       ├── websocket/                        # [M3]
│   │       └── database/                         # [M3]
│   │
│   ├── video-gateway/                            # [M1] MediaMTX configuration
│   │
│   ├── ai-worker/                                # [M2] Video processing and AI
│   │   ├── ingestion/                            # [M2]
│   │   ├── preprocessing/                        # [M2]
│   │   ├── detectors/                            # [M2]
│   │   │   ├── fire/                             # [M2]
│   │   │   ├── smoke/                            # [M2]
│   │   │   └── accident/                         # [M2]
│   │   ├── tracking/                             # [M2]
│   │   └── events/                               # [M2]
│   │
│   └── notification-worker/                      # [M3]
│
├── packages/
│   ├── shared-types/                             # [M4]
│   ├── api-client/                               # [M4]
│   └── ui/                                       # [M4]
│
├── infrastructure/
│   ├── docker/                                   # [M3]
│   ├── nginx/                                    # [M1]
│   └── monitoring/                               # [M3]
│
├── docs/
│   ├── architecture/                             # [M4]
│   ├── api/                                      # [M4]
│   ├── database/                                 # [M4]
│   └── ai-models/                                # [M2]
│
├── docker-compose.yml                            # [M3]
├── .env.example                                  # [M3]
├── .gitignore                                    # [M3]
└── README.md                                     # [M3]
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18+ or v20+
- **Python**: 3.10+
- **Docker & Docker Compose**

### 2. Environment Configuration
```bash
cp .env.example .env
```

### 3. Running with Docker Compose
```bash
docker compose up -d
```

### 4. Running Web Frontend Locally
```bash
npm install
npm --workspace=apps/web run dev
```
