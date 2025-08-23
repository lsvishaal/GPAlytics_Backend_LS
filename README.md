# 🎓 GPAlytics Backend - Sprint Roadmap

> **Modern FastAPI backend for academic performance tracking and analytics**

## 🚀 Project Status

- **Current Sprint**: Sprint 0 (Foundation)
- **Start Date**: August 12, 2025
- **Tech Stack**: FastAPI, PostgreSQL, JWT, Argon2, SQLAlchemy 2.0
- **Deployment**: Docker + Azure

---

## 📋 Sprint Backlog

### **Sprint 0: Foundation** (Week 1) 
**Goal**: MVP user authentication and basic infrastructure

#### **Epic: Core Infrastructure**
- [ ] **Project Setup**
  - [x] UV dependency management
  - [x] Core dependencies installed
  - [ ] Docker configuration
  - [ ] Database connection setup
  - [ ] Alembic migrations setup

- [ ] **Authentication System**
  - [ ] User registration endpoint
  - [ ] JWT token generation (PyJWT)
  - [ ] Password hashing (Argon2)
  - [ ] Login endpoint
  - [ ] Protected route middleware

- [ ] **Database Foundation**
  - [ ] SQLAlchemy 2.0 models (User)
  - [ ] Database connection async pool
  - [ ] Initial migration (users table)
  - [ ] Basic CRUD operations

#### **User Stories**
- **As a student**, I want to register an account so I can track my grades
- **As a student**, I want to login securely so my data is protected
- **As a developer**, I want proper error handling so debugging is easy

#### **Definition of Done**
- [ ] React frontend can register new users
- [ ] React frontend can login and receive JWT token
- [ ] Protected endpoints require valid JWT
- [ ] Passwords are hashed with Argon2
- [ ] All endpoints return consistent JSON responses
- [ ] Docker container runs locally

---

### **Sprint 1: Grade Management** (Week 2)
**Goal**: Complete grade CRUD operations with calculations

#### **Epic: Grade System**
- [ ] **Grade Models & Validation**
  - [ ] Course grade model (O, A+, A, B+, B, C, F)
  - [ ] Semester grouping
  - [ ] Credit validation (1-10 range)
  - [ ] Grade point mapping (O=10, A+=9, etc.)

- [ ] **Grade Operations**
  - [ ] Add single grade endpoint
  - [ ] Bulk grade entry (full semester)
  - [ ] Update existing grades
  - [ ] Delete grades
  - [ ] Get grades by semester

- [ ] **GPA Calculations**
  - [ ] Semester GPA calculation
  - [ ] Cumulative GPA (CGPA) calculation
  - [ ] Credit-weighted calculations
  - [ ] Real-time updates

#### **User Stories**
- **As a student**, I want to add my semester grades so I can track progress
- **As a student**, I want to see my calculated GPA so I know my performance
- **As a student**, I want to edit wrong grades so my records are accurate

#### **Definition of Done**
- [ ] Can add/edit/delete grades via React app
- [ ] GPA calculations match academic standards
- [ ] Bulk operations work for entire semesters
- [ ] Validation prevents invalid grades/credits
- [ ] Performance under 200ms for grade operations

---

### **Sprint 2: Analytics Foundation** (Week 3)
**Goal**: Personal performance analytics and insights

#### **Epic: Student Analytics**
- [ ] **Personal Insights**
  - [ ] Best/worst performing subjects
  - [ ] Semester-wise performance trends
  - [ ] Credit distribution analysis
  - [ ] Grade distribution charts

- [ ] **Performance Tracking**
  - [ ] GPA progression over semesters
  - [ ] Improvement/decline detection
  - [ ] Target GPA calculations
  - [ ] Academic warnings (low GPA)

#### **User Stories**
- **As a student**, I want to see my strongest subjects so I can focus on my strengths
- **As a student**, I want to track my improvement so I stay motivated
- **As a student**, I want academic insights so I can make better decisions

#### **Definition of Done**
- [ ] Analytics endpoints return structured data
- [ ] Charts render properly in React frontend
- [ ] Performance calculations are accurate
- [ ] Handles edge cases (no data, single semester)

---

### **Sprint 3: Batch Comparisons** (Week 4)
**Goal**: Social features and peer comparisons

#### **Epic: Competitive Analytics**
- [ ] **Batch Operations**
  - [ ] Percentile calculations within batch
  - [ ] Batch statistics (avg, median, std dev)
  - [ ] Top performers leaderboard
  - [ ] Anonymous peer comparisons

- [ ] **Performance Optimization**
  - [ ] Redis caching for expensive queries
  - [ ] Database indexing strategy
  - [ ] Batch query optimization
  - [ ] Response time improvements

#### **User Stories**
- **As a student**, I want to see my percentile rank so I know my relative performance
- **As a student**, I want to see top performers so I can set goals
- **As a student**, I want anonymous comparisons so I can benchmark privately

#### **Definition of Done**
- [ ] Percentile calculations accurate within batches
- [ ] Leaderboards update in real-time
- [ ] Caching reduces response times by 80%
- [ ] Handles large batch sizes (500+ students)

---

### **Sprint 4: ML Predictions** (Week 5)
**Goal**: Predictive analytics and future planning

#### **Epic: Intelligent Insights**
- [ ] **Grade Prediction**
  - [ ] Next semester GPA prediction
  - [ ] Linear regression model
  - [ ] Confidence intervals
  - [ ] Model accuracy tracking

- [ ] **Advanced Analytics**
  - [ ] Course difficulty analysis
  - [ ] Study pattern recommendations
  - [ ] Risk assessment (failing grades)
  - [ ] Goal achievement probability

#### **User Stories**
- **As a student**, I want GPA predictions so I can plan better
- **As a student**, I want course recommendations so I can optimize my schedule
- **As a student**, I want early warnings so I can prevent academic issues

---

### **Sprint 5: Production Ready** (Week 6)
**Goal**: Deployment, monitoring, and polish

#### **Epic: Production Operations**
- [ ] **Deployment Pipeline**
  - [ ] CI/CD with GitHub Actions
  - [ ] Docker multi-stage builds
  - [ ] Environment-specific configs
  - [ ] Health checks and monitoring

- [ ] **Security & Compliance**
  - [ ] Rate limiting implementation
  - [ ] Input sanitization audit
  - [ ] Security headers
  - [ ] Data backup strategy

- [ ] **Documentation & Testing**
  - [ ] API documentation (OpenAPI)
  - [ ] Integration tests
  - [ ] Performance tests
  - [ ] User guides

---

## 🎯 Success Metrics

### **Technical KPIs**
- **Response Time**: <200ms for 95% of requests
- **Uptime**: 99.9% availability
- **Test Coverage**: >80% code coverage
- **Security**: Zero critical vulnerabilities

### **Business KPIs**
- **User Adoption**: Registration rate from React app
- **Feature Usage**: Grade entry completion rate
- **Performance**: Analytics usage frequency
- **User Satisfaction**: Feedback scores

---

## 🛠️ Development Setup

```bash
# Quick start
git clone <repo>
cd GPAlytics_Backend_LS
uv sync
docker-compose up -d postgres
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

---

## 📱 Integration Status

- **Frontend**: React + Vite (existing)
- **Database**: PostgreSQL (local + production)
- **Deployment**: Docker + Railway/Render
- **Monitoring**: Built-in FastAPI metrics

---

## 🔄 Weekly Rhythm

- **Monday**: Sprint planning, task prioritization
- **Wednesday**: Mid-sprint check, blockers review  
- **Friday**: Sprint demo, retrospective
- **Daily**: 15min progress check, update task status

**Next Sprint Planning**: Every Friday 4-5 PM

---

*Last Updated: August 12, 2025*
*Sprint 0 - Foundation Phase*
