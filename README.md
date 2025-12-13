# 🏥 AI Med - ML API Infrastructure (Persistence Layer)

This repository provides the isolated **Persistence Layer** for the ML API, consisting of:
- **Redis** (Routing)
- **PostgreSQL** (Metadata/Analytics)

---

## 🏗️ Architecture

| Service | Role | Data Type |
|---------|------|-----------|
| **redis_routes** | Service Discovery. Ultra-fast routing lookup (Model Name → IP:Port) | Key-Value (Hash) |
| **postgres_meta** | Analytics Store. Model registry & time-series usage metrics for autoscaling | Relational |

---

## 🚀 Quick Start

1. Create a `.env` file (see [Configuration](#️-configuration))
2. Start the infrastructure:

```bash
docker-compose up -d
```

---

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=models_meta
POSTGRES_PORT=5432
REDIS_PORT=6379
```

---

## 🛠️ Manual Management ("Manager Mode")

Since the automated Manager is WIP, use CLI commands to register models manually.

### 1. Add Route (Redis)

Links a model name to a worker container IP.

```bash
docker exec -it redis_routes_db redis-cli
```

```redis
HSET model_routes digit-recognizer-v1 "172.18.0.5:8000"
```

### 2. Register Model & Metrics (PostgreSQL)

Tracks model existence and usage load.

```bash
docker exec -it postgres_meta_db psql -U admin -d models_meta
```

#### A. Register Model (Required first)

```sql
INSERT INTO model_registry (model_name) 
VALUES ('digit-recognizer-v1');
```

#### B. Log Usage (Time-Series Simulation)

```sql
INSERT INTO model_usage_metrics (model_name, time_window, request_count)
VALUES ('digit-recognizer-v1', '2025-12-13 14:15:00', 1);
```

---
### 3. Logging (CRITICAL: UPSERT Logic)
The Router **MUST** use an atomic **UPSERT** strategy for metrics to handle concurrent requests and avoid unique key violations. Do not use simple `INSERT`.

* **Logic:** Try to insert `1`. If the time bucket exists for this model, increment the counter instead of failing.
* **Required SQL Pattern:**
    ```sql
    INSERT INTO model_usage_metrics (model_name, time_window, request_count)
    VALUES (%s, %s, 1)
    ON CONFLICT (model_name, time_window)
    DO UPDATE SET request_count = model_usage_metrics.request_count + 1;
    ```

## 🔌 Router Integration Logic (Dev Guide)

For the future Router service:

1. **Discovery**: Query Redis (`HGET model_routes [name]`)
2. **Proxy**: Forward request to the obtained IP
3. **Logging**: Perform Async UPSERT to Postgres (Increment `request_count` for the current 15-min bucket)
