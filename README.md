# Social Empowerment Platform

An AI-powered camera monitoring and incident coordination platform that detects potential **fire**, **smoke**, and **road accidents**, then enables an Emergency Handler to review, verify, assign, and track incidents through resolution.

---

## 🎯 Key Principle

> **An AI detection is an event candidate, not a confirmed emergency.**  
> Human review is strictly required before any consequential action, dispatch, or response.

---

## 👥 Four-Person Team Allocation & Ownership

| Member | Focus Area | Directory Scope | Main Deliverables |
|---|---|---|---|
| **Member 1 [M1]** | Camera, Stream Gateway & Nginx | `services/video-gateway/`, `apps/web/src/features/camera/`, `services/api/app/devices/`, `services/api/app/streams/`, `infrastructure/nginx/` | Camera registration/location UI; `getUserMedia` preview and controls; WebRTC/MediaMTX video pipeline; device/stream APIs; stream health/reconnect. |
| **Member 2 [M2]** | AI & Computer Vision Worker | `services/ai-worker/`, `services/api/app/ai_detections/`, `docs/ai-models/` | Frame ingestion/sampling; fire, smoke, and road accident detectors (YOLO/OpenCV/ByteTrack); candidate event schema and publishing to Redis Streams; confidence scoring & evidence reference generation. |
| **Member 3 [M3]** | Backend Core, Incident Engine, Workers & Infra | `services/api/` (Auth, Users, Incidents, Assignments, Notifications, Analytics, WebSocket, Database), `services/notification-worker/`, `infrastructure/docker/`, `infrastructure/monitoring/`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md` | Authentication & RBAC; PostgreSQL/PostGIS schema and async session engine; Incident Engine (normalization, deduplication, correlation, severity scoring); verification/assignment/resolution lifecycle APIs; Redis Stream consumer; real-time WebSocket feeds; alert dispatcher worker; multi-container Docker Compose. |
| **Member 4 [M4]** | Handler Dashboard, UI & Shared Packages | `apps/web/` (App shell, Handler Dashboard, Admin section, Components), `packages/` (`shared-types`, `api-client`, `ui`), `docs/` (`architecture`, `api`, `database`) | The single unified Handler Dashboard; live camera feed + AI bounding boxes overlay; incident verification, assignment, response tracking & audit timeline UI; admin management; shared TypeScript types & API SDK. |

---

## 🏗 System Architecture & End-to-End Workflow

```
[ Laptop / USB Webcam ]
         │
         ▼ (WebRTC live streaming)
[ MediaMTX Gateway (sep-video-gateway) ]
         │
         ▼ (RTSP ingestion)
[ AI Worker (sep-ai-worker) ] ── (YOLO Fire, Smoke, Accident Detectors)
         │
         ▼ (XADD ai:events candidate stream)
[ Redis Streams Broker (sep-redis) ]
         │
         ▼ (XREADGROUP consumer)
[ Incident Engine in FastAPI (sep-api) ]
   ├── Spatial/Temporal Deduplication (10-min window)
   ├── Cross-Detection Correlation (Recurring occurrences)
   ├── Dynamic Severity Classification (Low / Medium / High / Critical)
   └── Immutable Audit Trail Logging (PostgreSQL)
         │
         ├─── (WebSocket /ws/incidents broadcast) ──────────┐
         │                                                  │
         ▼ (XADD sep:notifications)                         ▼
[ Notification Worker (sep-notification-worker) ]   [ Handler Dashboard (sep-web) ]
   ├── SMTP Email Alerts                               ├── 1. Review Candidate
   ├── Responder Webhooks                              ├── 2. Confirm / Reject / Merge
   └── SMS Gateways                                    ├── 3. Assign Authority / Team
                                                       ├── 4. Track Live Status & Notes
                                                       └── 5. Record Closure Resolution
```

---

## 🛠 Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS
- **Camera Transport**: WebRTC, Browser MediaDevices API, MediaMTX (bluenviron)
- **Backend API**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (AsyncIO), Alembic
- **AI / Computer Vision**: PyTorch, YOLO, OpenCV, ByteTrack
- **Event Queue & Message Broker**: Redis 7 (Redis Streams & Pub/Sub)
- **Database & Geospatial**: PostgreSQL 16 + PostGIS
- **Orchestration & Deployments**: Docker Compose, Nginx, Prometheus

---

## 🚀 Getting Started

### 1. Prerequisites
- **Docker & Docker Compose** (v2+)
- **Node.js** (v18+ or v20+)
- **Python** (v3.10+)

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Default configuration works out-of-the-box for local Docker Compose development.

### 3. Launch Platform via Docker Compose
```bash
docker compose up -d --build
```
This starts:
- `sep-postgres` on port `5432`
- `sep-redis` on port `6379`
- `sep-video-gateway` on ports `8554` (RTSP), `8888` (HLS), `8889` (WebRTC)
- `sep-api` on port `8000` (FastAPI Swagger Docs at `http://localhost:8000/docs`)
- `sep-ai-worker` (Background video detection pipeline)
- `sep-notification-worker` (Alert dispatcher)
- `sep-web` on port `3000` (`http://localhost:3000`)
- `sep-prometheus` on port `9090` (`http://localhost:9090`)

### 4. Default Seeded Accounts
Upon initial startup, the database automatically seeds default accounts:
- **Administrator**: `admin@socialtracker.org` / `admin123`
- **Emergency Handler**: `handler@socialtracker.org` / `handler123`

---

## 📡 API Reference Overview

### Authentication (`/api/auth`)
- `POST /api/auth/login`: Authenticate and receive JWT access token.
- `POST /api/auth/register`: Create user account.
- `GET /api/auth/me`: Get profile and role of authenticated user.
- `POST /api/auth/logout`: Invalidate session.

### Users Management (`/api/users`)
- `GET /api/users`: List users (requires handler or admin).
- `GET /api/users/{id}`: Get specific user details.
- `POST /api/users`: Create user with assigned role (admin only).
- `PATCH /api/users/{id}`: Update user name, role, or active status (admin only).
- `DELETE /api/users/{id}`: Deactivate user account (admin only).

### Incidents & Lifecycle (`/api/incidents`)
- `GET /api/incidents`: List incidents with multi-parameter filtering (`status`, `type`, `severity`, `camera_id`, `search`, pagination).
- `GET /api/incidents/{id}`: Retrieve comprehensive incident details, bounding boxes, evidence, and audit timeline.
- `POST /api/incidents/{id}/confirm`: Handler confirms AI candidate as a genuine emergency.
- `POST /api/incidents/{id}/reject`: Handler marks candidate as a false alarm / false positive.
- `POST /api/incidents/{id}/inconclusive`: Handler flags candidate as inconclusive pending further observation.
- `POST /api/incidents/{id}/merge`: Merges a duplicate incident into a primary target incident.
- `PATCH /api/incidents/{id}/status`: Transition incident status (`reviewing`, `dispatched`, `resolved`).
- `GET /api/incidents/{id}/timeline`: Retrieve complete chronological audit trail.

### Assignments & Response (`/api/assignments` & `/api/incidents/{id}/assignments`)
- `POST /api/incidents/{id}/assignments`: Dispatch confirmed incident to emergency team/authority.
- `GET /api/assignments`: List assignments with status and incident filters.
- `GET /api/assignments/{id}`: Get assignment details.
- `POST /api/assignments/{id}/acknowledge`: Responder acknowledges assignment with ETA and notes.
- `POST /api/assignments/{id}/progress`: Log on-scene updates (e.g., `en_route`, `on_scene`).
- `POST /api/assignments/{id}/resolve`: Record resolution outcome and automatically close the parent incident.

### Notifications (`/api/notifications`)
- `GET /api/notifications`: Retrieve user and system alert notifications.
- `PATCH /api/notifications/{id}/read`: Mark notification as read.
- `POST /api/notifications/read-all`: Mark all notifications as read.

### Analytics (`/api/analytics`)
- `GET /api/analytics/summary`: Aggregate counts, active emergencies, false alarms, and average response times.
- `GET /api/analytics/camera-stats`: Incident counts and activity per registered camera device.

### Real-time WebSocket (`/ws/incidents`)
- Connect at `ws://localhost:8000/ws/incidents` for real-time live events:
  - `incident_created`, `incident_correlated`, `incident_confirmed`, `incident_rejected`, `incident_assigned`, `incident_resolved`.

---

## 🧪 Testing

### Running Backend Unit & Integration Tests:
```bash
python -m unittest discover -s services/api/tests -p "test_*.py"
```

### Running AI Worker Tests:
```bash
python -m unittest discover -s services/ai-worker/tests -p "test_*.py"
```
