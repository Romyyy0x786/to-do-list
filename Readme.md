# 📝 Smart Task Manager (FARM Stack)

A full-stack Todo & Task Management application built using the **FARM Stack** (**F**astAPI, **R**eact, **M**ongoDB). This app supports user authentication, multiple project boards, and real-time task tracking.

![Project Status](https://img.shields.io/badge/Status-Completed-success)
![License](https://img.shields.io/badge/License-MIT-blue)

## 🚀 Tech Stack

### Frontend (Client-Side)
- **Framework:** React.js (Vite) + TypeScript
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios
- **State Management:** React Hooks (useState, useEffect)

### Backend (Server-Side)
- **Framework:** FastAPI (Python)
- **Database:** MongoDB Atlas (Cloud NoSQL)
- **Driver:** Motor (Async MongoDB Driver)
- **Authentication:** JWT (JSON Web Tokens) & OAuth2
- **Security:** Passlib (Bcrypt) for password hashing

---

## 🌟 Features

- **🔐 User Authentication:** Secure Sign Up & Login system.
- **📋 Kanban-Style Boards:** Create multiple boards (projects) to organize tasks.
- **✅ Task Management:** Add tasks, mark them as Completed/Pending, and delete them.
- **⚡ Real-time Updates:** Fast UI updates using React state and FastAPI.
- **📱 Responsive Design:** Clean UI built with Tailwind CSS.

---

## 🛠️ Installation & Run Guide

Follow these steps to run the project locally on your machine.

### Prerequisites
- Python 3.8+ installed
- Node.js installed
- MongoDB Atlas Connection String

### 1️⃣ Backend Setup
Open a terminal and navigate to the backend folder:

```bash
cd backend
```

---
```bash
Create a virtual environment:
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

```
---

```bash

pip install -r requirements.txt
```
---
```bash
Start the Server:
python -m uvicorn main:app --reload
```
---
```bash
Frontend Setup
cd frontend
```
---
```bash
Install dependencies:
npm install
```
---
```bash
Start the React App:
npm run dev
```

---


