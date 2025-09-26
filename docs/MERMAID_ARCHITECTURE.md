# Updated Architecture Diagram (Mermaid)

```mermaid
flowchart TD
    subgraph Client[Client Layer]
      FE[React (Vite + TypeScript)]
    end

    FE -->|HTTP/REST| API

    subgraph API[FastAPI Application]
      direction TB
      CORS[CORS Middleware]
      Health[Health Endpoints]
      API --> CORS
      API --> Health

      subgraph Controllers[HTTP Controllers]
        AUTH_C[Auth Controller]
        GRADES_C[Grades Controller]
        ANALYTICS_C[Analytics Controller]
        USERS_C[Users Controller]
      end

      subgraph Services[Business Services]
        AUTH_S[Auth Service]
        GRADES_S[Grades Service]
        ANALYTICS_S[Analytics Service]
        USERS_S[Users Service]
        OCR_S[OCR Service (Gemini Vision)]
      end

      subgraph Core[Core Utilities]
        CFG[config.py (Pydantic Settings)]
        DB[database.py (Async Engine + DI)]
        SEC[security.py (JWT, hashing)]
        EXC[exceptions.py]
      end

      Controllers -->|calls| Services
      Services -->|uses| Core
      GRADES_S -->|invokes| OCR_S

    end

    subgraph Data[Data Layer]
      SQL[(Azure SQL Database)]
      ENT[Entities (SQLModel)]
    end

    Services -->|CRUD via SQLModel| ENT --> SQL

    subgraph Infra[Infrastructure]
      Docker[Docker Containers]
      Redis[(Redis - docker-compose ready)]
      Azure[Azure Cloud Services]
    end

    API -.deployed in.-> Docker -.hosted on.-> Azure
    Services -.optional cache.-> Redis
```

Notes:
- This diagram mirrors the current code: four domain controllers/services, OCR (Gemini), entities, and core utilities.
- Redis is provisioned in `docker/docker-compose.yml` but optional in code right now.
