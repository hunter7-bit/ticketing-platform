TixMaster: High-Concurrency Event Ticketing Platform 🎫

A production-grade event ticketing platform designed to handle massive traffic spikes and prevent double-booking using advanced database row-level locking and real-time WebSocket broadcasting.

🏗️ System Architecture

This project solves the classic "Ticketing Concurrency Problem" (where multiple users attempt to buy the exact same seat simultaneously) by implementing a distributed locking architecture.

Key Features

PostgreSQL Row-Level Locking: Utilizes SELECT ... FOR UPDATE SKIP LOCKED to instantly find and reserve available tickets without causing database bottlenecks or deadlocks.

Redis TTL Cart Expiration: When a ticket is reserved, a 15-second TTL (Time-To-Live) key is set in Redis.

Asynchronous Background Worker: A standalone Python worker listens to Redis Keyspace Notifications for expired locks and asynchronously reverts abandoned tickets in Postgres back to AVAILABLE.

Real-Time WebSockets: A FastAPI WebSocket manager actively broadcasts capacity updates to all connected React clients, providing a live "Tickets Remaining" countdown without page refreshes.

JWT Authentication: Secure user sessions using hashed passwords (bcrypt) and OAuth2 Bearer tokens.

💻 Tech Stack

Backend: Python 3.11, FastAPI, SQLAlchemy (Async), asyncpg, Uvicorn

Database: PostgreSQL 15 (Alpine)

Cache & Message Broker: Redis 7 (Alpine)

Frontend: React, Vite, Tailwind CSS, Lucide Icons

Infrastructure: Docker, Docker Compose

🚀 Getting Started

Prerequisites

Docker and Docker Compose

Node.js (v18+)

1. Start the Backend Infrastructure

The backend, database, cache, and background worker are all containerized.

# Clone the repository
git clone https://github.com/YOUR_USERNAME/ticketing-platform.git
cd ticketing-platform

# Boot up the backend infrastructure
docker-compose up -d --build


2. Seed the Database

Populate the PostgreSQL database with the test event ("Oikotaan Festival") and pre-allocate the ticket rows.

docker-compose exec api python -m app.db.seed


3. Start the Frontend

(Note: Frontend Dockerization is in progress. Currently run via Vite.)

cd frontend
npm install
npm run dev


The application will be available at http://localhost:5173.
API Documentation (Swagger UI) is available at http://localhost:8000/docs.

📂 Repository Structure

ticketing-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI Routes & WebSockets
│   │   ├── core/         # JWT Security & Config
│   │   ├── db/           # Async SQLAlchemy Engine & Seeder
│   │   ├── models/       # Postgres ORM Models
│   │   ├── schemas/      # Pydantic Validation Schemas
│   │   └── workers/      # Redis TTL Expiration Listener
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main React Application
│   │   └── index.css     # Tailwind Directives
│   ├── package.json
│   └── tailwind.config.js
└── docker-compose.yml    # Multi-container orchestration


🧪 Testing the Concurrency

Open two browser windows side-by-side (e.g., Chrome and Incognito).

Log in and click "Add to Cart" in Window A.

Observe the live ticket count drop instantly in Window B via WebSockets.

Wait 15 seconds without completing the checkout.

The Redis Worker will detect the timeout, unlock the database row, and trigger a WebSocket broadcast, instantly reverting the ticket count on both screens.

📝 License

This project is open-source and available under the MIT License.