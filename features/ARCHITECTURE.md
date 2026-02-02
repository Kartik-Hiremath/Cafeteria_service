# Architecture Documentation

## Data Flow Diagram (DFD)

```mermaid
flowchart LR
    User((User)) -->|Login/Book| System[Booking System]
    System -->|Auth| IBM[IBM W3ID]
    System <-->|Read/Write| DB[(Database)]
```

## System Architecture

```mermaid
flowchart TB
    subgraph Client
        FE[Frontend React + Vite :3000]
    end
    subgraph Server
        BE[Backend FastAPI :8000]
    end
    subgraph Data
        DB[(SQLite cafeteria.db)]
    end
    IBM[IBM W3ID SSO]
    FE -->|API + credentials| BE
    BE -->|OAuth| IBM
    BE <-->|SQLAlchemy| DB
```

## Component Overview

| Component | Technology | Port |
|-----------|------------|------|
| Frontend | React, Vite, Tailwind | 3000 |
| Backend | FastAPI | 8000 |
| Database | SQLite (dev) / PostgreSQL (prod) | - |
| Auth | IBM W3ID OIDC | - |

Diagrams above are in Mermaid format and render in GitHub, VS Code, and most markdown viewers. No additional install required.
