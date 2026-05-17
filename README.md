# 🛡️ FraudEye Pro: Cybersecurity SaaS Platform

FraudEye Pro is a comprehensive, production-ready financial fraud detection platform. It combines state-of-the-art machine learning with a modern full-stack architecture to provide real-time threat intelligence.

---

## 🏗️ Architecture Overiview

```bash
financial-fraud-cybersecurity/
├── backend/                # FastAPI High-Performance Backend
│   ├── auth/               # JWT & Password Security
│   ├── database/           # SQLite (SQLAlchemy ORM)
│   ├── fraud_engine/       # Original ML Scripts & Analysis
│   ├── routes/             # API Endpoints (Auth, Fraud, Analytics)
│   └── main.py             # Server Entry Point
├── frontend/               # React SaaS Dashboard
│   ├── src/pages/          # Landing, Login, Dashboard
│   └── package.json        # Frontend Dependencies
├── ml_models/              # Trained ML Sentinel Models
├── notebooks/              # Cybersecurity Analysis & Research
└── dashboards/             # Legacy PowerBI/Kibana Exports
```

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm start
```

## ✨ Core SaaS Features
- **JWT Authentication**: Secure, token-based user sessions.
- **Real-time ML Scoring**: Instant fraud risk assessment via REST API.
- **Audit Logging**: Every transaction is logged for compliance (PCI-DSS/RBI).
- **Interactive Dashboard**: Live threat feed and security analytics.
- **Modular Fraud Engine**: Easily plug in new detection rules or ML models.

---
Built by Sneha Arora — Professional Portfolio Project
