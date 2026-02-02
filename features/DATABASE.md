# Database Documentation

## Overview

The Cafeteria Booking system uses **SQLite** by default (file-based, **persistent**). For production, PostgreSQL can be used via `DATABASE_URL`.

**Persistence**: Yes. SQLite writes to `cafeteria.db` on disk. Data survives app restarts.

## Entity-Relationship Diagram

```mermaid
erDiagram
    users ||--o{ reservations : makes
    managers ||--o{ charges : "has charges"
    seats ||--o{ reservations : "booked in"
    timeslots ||--o{ reservations : "scheduled for"
    reservations ||--o{ charges : "generates"
    users {
        int id PK
        string employee_uid UK
        string email
        string manager_name FK
    }
    managers {
        int id PK
        string manager_name UK
        decimal balance
    }
    seats {
        int id PK
        string label
    }
    timeslots {
        int id PK
        datetime starts_at
        datetime ends_at
    }
    reservations {
        int id PK
        int user_id FK
        int seat_id FK
        int timeslot_id FK
        enum status
        datetime available_at
    }
    charges {
        int id PK
        int manager_id FK
        int reservation_id FK
        decimal amount
    }
```

## Database File

- **Location**: `features/cafeteria.db` (when running from `features/` directory)
- **Format**: SQLite 3
- **Persistence**: Yes. Data is written to disk and survives app restarts.

## Persistence Verification

### 1. Check file exists and has content
```bash
cd features
ls -la cafeteria.db
# Should show file size > 0
```

### 2. Verify data survives restart
```bash
# Start backend, create a booking via UI
# Stop backend (Ctrl+C)
# Restart backend
# Check admin dashboard - booking should still be there
```

### 3. Query directly with sqlite3
```bash
cd features
sqlite3 cafeteria.db "SELECT COUNT(*) FROM users;"
sqlite3 cafeteria.db "SELECT manager_name, balance FROM managers;"
sqlite3 cafeteria.db ".tables"
```

### 4. Integrity check
```bash
sqlite3 cafeteria.db "PRAGMA integrity_check;"
# Should return: ok
```

## ACID Properties

| Property | Implementation |
|----------|----------------|
| **Atomicity** | Transactions: `db.commit()` on success, `db.rollback()` on exception. Reservation + Charge + balance updates occur in one transaction. |
| **Consistency** | Unique constraints (`uq_user_timeslot`, `uq_seat_timeslot`), check constraints on balances. |
| **Isolation** | SQLite uses `SERIALIZABLE` (default). Concurrent requests are serialized. |
| **Durability** | SQLite writes to disk. `PRAGMA journal_mode=WAL` can be used for better concurrency. |

## Schema

### users
- id, employee_uid, email, first_name, last_name, manager_name

### managers
- id, manager_name, balance

### seats
- id, label (A1–J10)

### timeslots
- id, starts_at, ends_at

### reservations
- id, user_id, seat_id, timeslot_id, status, created_at, available_at
- Unique: (user_id, timeslot_id), (seat_id, timeslot_id)

### charges
- id, manager_id, reservation_id, amount, created_at

## Access Methods

### 1. SQLite CLI
```bash
sqlite3 cafeteria.db
.tables
.schema reservations
SELECT * FROM managers;
.quit
```

### 2. Python
```python
import sqlite3
conn = sqlite3.connect("cafeteria.db")
cur = conn.cursor()
cur.execute("SELECT * FROM managers")
print(cur.fetchall())
conn.close()
```

### 3. API (Swagger)
- http://localhost:8000/docs
- `GET /reservations/verify` – system status
- `GET /admin/dashboard` – all data

## Configuration

Set in `.env`:
```env
DATABASE_URL=sqlite:///./cafeteria.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost:5432/cafeteria
```
