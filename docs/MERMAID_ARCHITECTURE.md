# Current System Architecture (Mermaid)

```mermaid
flowchart TD
    subgraph Client[Client Applications]
      FE[Frontend (React/Vue/Mobile)]
      API_CLIENT[API Clients]
    end

    Client -->|HTTP/REST| GATEWAY[API Gateway]
    
    subgraph APP[FastAPI Application - src/app/main.py]
      direction TB
      MIDDLEWARE[CORS & Security Middleware]
      HEALTH[Health Checks - src/shared/health.py]
      
      GATEWAY --> MIDDLEWARE
      MIDDLEWARE --> HEALTH
      
      subgraph ROUTERS[HTTP Routers - src/routers/]
        AUTH_API[🔐 Auth API<br/>Login, Register, Tokens]
        USERS_API[👤 Users API<br/>Profile Management]
        GRADES_API[📊 Grades API<br/>Upload, OCR, CRUD]
        ANALYTICS_API[📈 Analytics API<br/>CGPA, Reports]
      end
      
      subgraph SERVICES[Business Services]
        AUTH_SVC[Auth Service<br/>JWT, Password Hashing]
        USERS_SVC[Users Service<br/>Profile Logic]
        GRADES_SVC[Grades Service<br/>Data Validation]
        ANALYTICS_SVC[Analytics Service<br/>Calculations]
        OCR_SVC[🤖 OCR Service<br/>Gemini Vision API]
      end
      
      subgraph CORE[Core Infrastructure - src/shared/]
        CONFIG[config.py<br/>Environment Settings]
        DATABASE[database.py<br/>Async SQLModel]
        SECURITY[security.py<br/>JWT & Crypto]
        ENTITIES[entities.py<br/>Data Models]
        EXCEPTIONS[exceptions.py<br/>Error Handling]
      end
      
      MIDDLEWARE --> ROUTERS
      ROUTERS --> SERVICES
      SERVICES --> CORE
      GRADES_SVC --> OCR_SVC
    end

    subgraph DATA[Data Layer]
      AZURE_SQL[(Azure SQL Database<br/>Production)]
      MODELS[SQLModel Entities<br/>User, Grade, RefreshToken]
    end

    subgraph EXTERNAL[External Services]
      GEMINI[🧠 Google Gemini Vision<br/>OCR Processing]
      AZURE_CLOUD[☁️ Azure Cloud Platform]
    end

    CORE --> MODELS --> AZURE_SQL
    OCR_SVC --> GEMINI
    AZURE_SQL --> AZURE_CLOUD

    subgraph DEPLOYMENT[Deployment & Infrastructure]
      DOCKER[🐳 Docker Containers]
      REDIS[(Redis Cache<br/>Optional)]
      MONITORING[Health & Monitoring]
    end

    APP -.deployed as.-> DOCKER
    DOCKER -.hosted on.-> AZURE_CLOUD
    SERVICES -.future cache.-> REDIS
    HEALTH --> MONITORING

    classDef apiClass fill:#e1f5fe
    classDef serviceClass fill:#f3e5f5
    classDef coreClass fill:#fff3e0
    classDef dataClass fill:#e8f5e8
    classDef externalClass fill:#fce4ec
    
    class AUTH_API,USERS_API,GRADES_API,ANALYTICS_API apiClass
    class AUTH_SVC,USERS_SVC,GRADES_SVC,ANALYTICS_SVC,OCR_SVC serviceClass
    class CONFIG,DATABASE,SECURITY,ENTITIES,EXCEPTIONS coreClass
    class AZURE_SQL,MODELS,REDIS dataClass
    class GEMINI,AZURE_CLOUD externalClass
```

## Architecture Notes

**Current Implementation (September 2025)**:
- ✅ Active routes in `src/routers/` with full functionality
- ✅ Shared core utilities in `src/shared/`
- ⚠️ Legacy `src/features/` exists but being phased out
- 🔄 Tests need restructuring to match new organization

**Key Design Decisions**:
- **Feature-based routing** - Each domain has dedicated router + service
- **Async-first** - All database operations use async/await
- **Type safety** - SQLModel provides end-to-end typing
- **Cloud-native** - Built for Azure with Docker deployment
- **API-first** - OpenAPI/Swagger documentation auto-generated

**Data Flow**:
1. HTTP Request → Router → Service → Database
2. OCR uploads: Router → OCR Service → Gemini Vision → Grade Service → Database
3. Analytics: Router → Analytics Service → Aggregate Queries → Response
