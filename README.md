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
DATABASE_URL=sqlite+aiosqlite:///./sql_app.db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend
No additional configuration needed for development.

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
