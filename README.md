# DocAI Platform

A modern SaaS platform for document conversion and AI-powered assistance.

## 🚀 Features

- **Document Conversion**: Convert between PDF, Word, PNG, XML, and more
- **AI Assistant**: Intelligent help with document formatting and editing
- **Modern UI**: Responsive design with dark/light themes
- **Authentication**: Secure JWT-based authentication
- **Freemium Model**: 3 free conversions, then upgrade to premium

## 🛠️ Tech Stack

### Frontend
- React 19 with TypeScript
- Vite for blazing-fast development
- Zustand for state management
- Lucide React for icons
- CSS Modules with CSS Variables

### Backend
- Python 3.12 + FastAPI
- SQLite database (SQLAlchemy + aiosqlite)
- JWT authentication
- OpenAI integration ready

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run development server
uvicorn main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 🔧 Configuration

### Backend (.env)
Create a `.env` file in the `backend/` directory:

```env
# No definir DATABASE_URL: la app usa por defecto backend/sql_app.db (ruta absoluta)
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO
```

**Production:** Set `SECRET_KEY` to a strong random value. The app logs a warning at startup if the default is used.

### Frontend
Optional: create `frontend/.env` to point to a different backend:

```env
VITE_API_URL=http://localhost:8000
```

If unset, the app uses the same host as the page with port 8000.

## 📸 Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Dark Mode
![Dark Mode](screenshots/dark-mode.png)

## 🚀 Deployment

### AWS Free Tier (Recommended)
- EC2 t2.micro instance
- RDS PostgreSQL (optional, currently using SQLite)
- S3 for file storage
- CloudFront for CDN

### Production Build

```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
# Use Gunicorn or Uvicorn with systemd
```

## 📝 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

**For developers:** Architecture, layers, conventions, and how to add endpoints or features: [Technical README (docs/README-TECH.md)](docs/README-TECH.md).

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📄 License

MIT License - feel free to use this project for learning or commercial purposes.

## 👨‍💻 Author

Built with ❤️ using Antigravity AI

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## ⭐ Show your support

Give a ⭐️ if this project helped you!
