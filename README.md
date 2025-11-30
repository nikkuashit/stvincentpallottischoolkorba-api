# 🎓 School Management API

Django REST Framework API for multi-school management system with JWT authentication and Swagger documentation.

## 🚀 Features

- ✅ **Django REST Framework** - Full-featured REST API
- ✅ **JWT Authentication** - Secure token-based auth with dj-rest-auth
- ✅ **Swagger/OpenAPI** - Interactive API documentation
- ✅ **CORS Configured** - Ready for frontend integration
- ✅ **Django Admin** - Powerful admin panel
- ✅ **SQLite Database** - Easy development setup

## 📋 Requirements

- Python 3.9+
- Pipenv

## 🛠️ Installation

### 1. Install Dependencies

```bash
# Install Pipenv if not installed
pip install --user pipenv

# Install project dependencies
pipenv install
```

### 2. Setup Environment

```bash
# .env file is already created with default values
# Modify if needed
```

### 3. Run Migrations

```bash
pipenv run python manage.py migrate
```

### 4. Create Superuser

```bash
pipenv run python create_superuser.py
```

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 🏃‍♂️ Running the Server

```bash
# Start development server
pipenv run python manage.py runserver

# Server will start at http://127.0.0.1:8000/
```

## 📚 API Documentation

Once the server is running, visit:

### Swagger UI (Interactive)
```
http://127.0.0.1:8000/swagger/
```

### ReDoc (Alternative Documentation)
```
http://127.0.0.1:8000/redoc/
```

### Django Admin Panel
```
http://127.0.0.1:8000/admin/
```

## 🔐 Authentication Endpoints

### Register New User
```
POST /api/auth/registration/
{
  "username": "user",
  "email": "user@example.com",
  "password1": "securepass123",
  "password2": "securepass123"
}
```

### Login
```
POST /api/auth/login/
{
  "username": "user",
  "password": "securepass123"
}
```

### Logout
```
POST /api/auth/logout/
Headers: Authorization: Bearer <access_token>
```

### Refresh Token
```
POST /api/auth/token/refresh/
{
  "refresh": "<refresh_token>"
}
```

## 🏗️ Project Structure

```
stvincentpallottischoolkorba-api/
├── school_api/           # Main project settings
│   ├── settings.py      # Django settings with DRF, JWT, CORS
│   ├── urls.py          # URL configuration with Swagger
│   └── wsgi.py
├── manage.py            # Django management script
├── Pipfile              # Dependencies
├── .env                 # Environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## 🔧 Configuration

### Settings Highlights

- **REST Framework**: Configured with JWT auth and pagination
- **JWT Tokens**:
  - Access token lifetime: 1 hour
  - Refresh token lifetime: 7 days
  - Automatic rotation enabled
- **CORS**: Enabled for all origins in development
- **Media Files**: Configured for image/file uploads

### Environment Variables (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173
```

## 📦 Installed Packages

- **django** - Web framework
- **djangorestframework** - REST API framework
- **django-rest-framework-simplejwt** - JWT authentication
- **dj-rest-auth** - Authentication endpoints
- **django-allauth** - User registration
- **django-cors-headers** - CORS handling
- **drf-yasg** - Swagger/OpenAPI documentation
- **python-decouple** - Environment variable management
- **pillow** - Image processing
- **requests** - HTTP library

## 🎯 Next Steps

1. **Create School App**
   ```bash
   pipenv run python manage.py startapp schools
   ```

2. **Define Models** - Create database models for:
   - School
   - Navigation Menu
   - Sections (About, News, Events, etc.)
   - Media Files

3. **Create Serializers** - Convert models to JSON

4. **Build ViewSets** - Create API endpoints

5. **Configure URLs** - Add routes to urls.py

## 🧪 Testing API

### Using Swagger UI
1. Go to http://127.0.0.1:8000/swagger/
2. Click "Authorize" button
3. Login to get JWT token
4. Use Bearer token format: `Bearer <your_token>`
5. Test all endpoints interactively

### Using cURL

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password1":"testpass123","password2":"testpass123"}'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"testpass123"}'
```

## 🔒 Security Notes

- Change `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure specific `ALLOWED_HOSTS`
- Use HTTPS in production
- Set `JWT_AUTH_HTTPONLY=True` for production
- Configure specific CORS origins

## 📝 License

MIT License

## 👥 Contributors

School Management API Team
