# 🎓 Technical Interview Guide: FraudEye Pro
Use this guide to prepare for high-level interviews for Cybersecurity, Fraud Analyst, or Full-Stack Engineer roles.

---

### 1. "Can you explain the architecture of FraudEye Pro?"
**Answer**: "FraudEye Pro is a multi-tier SaaS platform. The frontend is built with **React** and **Tailwind CSS**, providing a real-time 'Midnight SOC' dashboard. The backend uses **FastAPI** for high-concurrency request handling. For the intelligence layer, I implemented a **Hybrid-ML engine** that combines heuristic rules with a **Random Forest** classifier. Every transaction is processed through this engine, audit-logged in **PostgreSQL/SQLite**, and secured via **JWT authentication**."

### 2. "Why did you choose FastAPI over Flask or Django?"
**Answer**: "FastAPI was chosen for its native support for **asynchronous programming** and its automatic **Data Validation (Pydantic)**. In a fraud detection scenario, latency is critical—FastAPI's performance allows us to keep prediction times under 40ms, which is essential for preventing fraudulent flows before they are finalized."

### 3. "What is the 'Explainable AI' component in your project?"
**Answer**: "I wanted to solve the 'Black Box' problem in AI. In my platform, I implemented an **XAI Module** that analyzes the machine learning features for every prediction. It identifies the top drivers for a 'Fraud' flag—such as account draining or extreme amounts—and displays these as human-readable 'Rationales' on the dashboard. This empowers SOC analysts to make faster, more confident decisions."

### 4. "How does your project handle Compliance (PCI-DSS/RBI)?"
**Answer**: "I mapped the system's architecture to specific regulatory requirements. For example, **PCI-DSS 10.2** requires rigorous audit trails, so I built a `TransactionAudit` table that logs every prediction and analyst action. For **RBI guidelines on real-time monitoring**, I implemented a live-polling dashboard that updates every 5 seconds with new threat data."

### 5. "How did you handle the 500MB Vercel Deployment limit?"
**Answer**: "Initially, the bundle was too large due to heavy libraries like CatBoost. I optimized the system by switching to **Scikit-Learn** for the production model and removing **Pandas** in favor of **NumPy** for feature engineering. This reduced the footprint by 80% while maintaining the core detection accuracy."

### 6. "What would you add to this project if you had more time?"
**Answer**: "I would implement **Distributed Tracing** using OpenTelemetry to monitor the lifecycle of a transaction across microservices, and I'd add **Supabase for multi-tenant Auth**, allowing different banks to use the same platform while keeping their data completely isolated."
