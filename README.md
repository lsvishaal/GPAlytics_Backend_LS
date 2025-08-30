# GPAlytics Backend - Core Business Flow 📊

## 🎯 **Project Vision**
An intelligent GPA analytics platform that processes grade sheets using OCR + AI, then provides comprehensive academic insights.

## 🔄 **Core Business Flow**

### **Phase 1: User Authentication** 
```
POST /auth/register → User Registration
POST /auth/login    → User Login  
GET  /auth/profile  → Protected Profile Access
```

### **Phase 2: Grade Sheet Processing (Core Innovation)**
```
POST /upload/grade-sheet → Upload image/PDF
     ↓
OCR Extraction (messy text)
     ↓  
Gemini API Cleanup (structured data)
     ↓
Store in Database (user's grades)
```

### **Phase 3: Analytics & Insights**
```
GET /grades/semester/{id}     → View semester grades
GET /grades/cgpa             → Calculate CGPA
GET /grades/percentile       → Rank among peers
GET /grades/predictions      → Next semester predictions
GET /grades/analytics        → Min/Max GPA insights
```

---

## 🏗️ **API Endpoints (Priority Order)**

### **MVP Endpoints (Build First)**
1. `POST /auth/register` - User registration ✅
2. `POST /auth/login` - User authentication ✅
3. `POST /upload/grade-sheet` - Core feature: Upload & process grades ⏳
4. `GET /grades/cgpa` - View calculated CGPA ⏳
5. `GET /grades/analytics` - Basic analytics ⏳

### **Enhancement Endpoints (Build Later)**
6. `GET /grades/percentile` - Peer comparison
7. `GET /grades/predictions` - AI predictions
8. `POST /grades/manual-entry` - Manual grade entry
9. `GET /grades/export` - Export data

---

## 🚀 **Development Sprint Plan**

### **Sprint 1: Authentication Foundation** ✅
- ✅ User registration/login
- ✅ JWT token management
- ✅ Basic validation

### **Sprint 2: Core Upload Feature** ⏳ 
- 📤 File upload endpoint
- 🔍 OCR integration
- 🤖 Gemini API integration
- 💾 Grade storage

### **Sprint 3: Analytics Engine**
- 📊 GPA/CGPA calculation
- 📈 Basic analytics
- 🎯 Percentile calculation

### **Sprint 4: Advanced Features**
- 🔮 Predictions
- 📋 Manual entry
- 🎨 Enhanced analytics

---

## 🔥 **Key Differentiators**

1. **AI-Powered OCR Cleanup** - Gemini API fixes messy OCR output
2. **Automated Grade Extraction** - No manual data entry needed
3. **Peer Analytics** - Compare with batch mates
4. **Predictive Insights** - AI predicts next semester performance

---

## 🚀 **Quick Start**

## 📁 **Project Structure**

```
GPAlytics_Backend_LS/
├── app/                          # 🎯 Main application
│   ├── main.py                   # FastAPI app entry point
│   ├── auth.py                   # Authentication logic
│   ├── database.py               # Database manager
│   ├── models.py                 # SQLModel data models
│   └── utils/                    # Utility modules
│       ├── app_logging.py        # Logging configuration
│       └── rate_limiting.py      # Rate limiting
├── tests/                        # 🧪 All tests
│   ├── test_auth.py              # Authentication tests
│   ├── test_auth_pytest.py       # Pytest-based auth tests
│   ├── test_auth_unit.py         # Unit tests
│   ├── test.py                   # General tests
│   └── conftest.py               # Pytest configuration
├── docker/                       # 🐋 Docker configuration
│   ├── Dockerfile                # Multi-stage optimized build
│   ├── docker-compose.yml        # Dev/prod environments
│   ├── .dockerignore             # Docker build exclusions
│   └── init.sql                  # SQL Server initialization
├── scripts/                      # 🛠️ Development tools
│   └── dev.py                    # Cross-platform dev script
├── logs/                         # 📝 Application logs
├── .env                          # ⚙️ Environment configuration
├── .env.example                  # 📋 Environment template
├── pyproject.toml                # 📦 UV project config
└── README.md                     # 📖 This file
```

## 🛠️ **Development Commands**

### **Setup & Installation**
```powershell
# Check prerequisites
python scripts/dev.py check

# Install dependencies with UV (10x faster than pip!)
python scripts/dev.py install
```

### **Local Development**
```powershell
# Start local development server
python scripts/dev.py dev

# Run tests
python scripts/dev.py test
```

### **Docker Development**
```powershell
# Start full development environment (recommended)
python scripts/dev.py docker-dev

# Start production environment
python scripts/dev.py docker-prod

# Stop all Docker services
python scripts/dev.py docker-stop

# View logs
python scripts/dev.py logs
```

### **Utilities**
```powershell
# Check service health
python scripts/dev.py health

# Clean up Docker resources
python scripts/dev.py clean
```

## 🔗 **Service URLs**

| Service | Development | Production |
|---------|-------------|------------|
| **API** | http://localhost:8000 | http://localhost:8000 |
| **Docs** | http://localhost:8000/docs | http://localhost:8000/docs |
| **Health** | http://localhost:8000/health | http://localhost:8000/health |
| **SQL Server** | localhost:1433 | (External DB) |

## 🗃️ **Database Configuration**

### **Azure SQL Database** (Production)
```env
DATABASE_URL="mssql+aioodbc://username:password@server.database.windows.net:1433/database?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
```

### **Local Docker SQL Server** (Development)
```env
DATABASE_URL="mssql+aioodbc://sa:GPAlytics2024!@localhost:1433/GPAlytics?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
```

## 🧪 **Testing**

### **Run All Tests**
```powershell
python scripts/dev.py test

# Or with UV directly
uv run pytest tests/ -v
```

### **Run Specific Tests**
```powershell
uv run pytest tests/test_auth.py -v
uv run pytest tests/test_auth_pytest.py::test_user_registration -v
```

### **Test Coverage**
```powershell
uv add --dev pytest-cov
uv run pytest tests/ --cov=app --cov-report=html
```

## 🐋 **Docker Benefits**

### **Why This Setup?**
1. **⚡ UV Package Manager**: 10x faster installs than pip
2. **🔧 Multi-stage Builds**: Smaller production images (50% reduction)
3. **🔒 Security**: Non-root user, minimal attack surface
4. **🔄 Hot-reload**: Development container with live code updates
5. **🏥 Health Checks**: Built-in service monitoring
6. **🌐 Azure SQL Ready**: Same driver for local and cloud databases

### **Image Sizes**
- **With pip**: ~800MB
- **With UV**: ~400MB (50% smaller!)

## 🚀 **Production Deployment**

### **Build Production Image**
```powershell
cd docker
docker build -t gpalytics-backend .
```

### **Run with External Database**
```powershell
docker run -p 8000:8000 \
  -e DATABASE_URL="your-azure-sql-connection" \
  -e JWT_SECRET_KEY="your-production-secret" \
  gpalytics-backend
```

### **Docker Compose Production**
```powershell
cd docker
docker compose --profile prod up -d
```

## ⚙️ **Environment Variables**

```env
# Database
DATABASE_URL="mssql+aioodbc://..."

# JWT Configuration
JWT_SECRET_KEY="your-super-secret-key"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=30

# Application
DEBUG=true
PORT=8000
```

## 📚 **API Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint |
| `GET` | `/health` | Application health |
| `GET` | `/health/db` | Database health |
| `POST` | `/auth/register` | User registration |
| `POST` | `/auth/login` | User login |
| `GET` | `/docs` | Interactive API docs |

## 🔧 **Development Workflow**

1. **Start Development Environment**:
   ```powershell
   python scripts/dev.py docker-dev
   ```

2. **Make Changes**: Edit files in `app/` directory

3. **Test Changes**: Hot-reload automatically updates the container

4. **Run Tests**:
   ```powershell
   python scripts/dev.py test
   ```

5. **Check Health**:
   ```powershell
   python scripts/dev.py health
   ```

## 🎯 **Key Features**

- ✅ **Clean Architecture**: Organized into logical modules
- ✅ **Fast Development**: UV package manager + Docker hot-reload
- ✅ **Azure SQL Compatible**: Production-ready database integration
- ✅ **Comprehensive Testing**: Unit, integration, and health tests
- ✅ **Security First**: JWT authentication, password hashing, non-root containers
- ✅ **Monitoring Ready**: Health checks and structured logging
- ✅ **Production Optimized**: Multi-stage Docker builds, minimal images

## 🚦 **Project Status**

- **✅ Authentication**: Registration, login, JWT tokens
- **✅ Database**: SQLModel, async operations, health checks
- **✅ Docker**: Optimized multi-stage builds with UV
- **✅ Testing**: Comprehensive test suite with pytest
- **✅ Documentation**: Interactive API docs with FastAPI

## 📞 **Support**

- **Documentation**: Visit `/docs` when server is running
- **Health Check**: Visit `/health` to verify service status
- **Logs**: Check `logs/` directory for application logs

---

**🚀 Ready to build amazing things with GPAlytics Backend!**
