# Cafeteria Seat Booking System - Blu-Reserve

A comprehensive cafeteria seat booking system with 100 seats. Users login with IBM w3id SSO, book seats for timeslots, and the system charges Blu-Dollars to their manager account.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/siddharthpuhan-ibm/Cafeteria-Service.git
cd Cafeteria-Service
```

2. **Backend Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # If .env.example exists
# Edit .env with your configuration
```

3. **Frontend Setup**
```bash
cd Frontend
npm install
```

4. **Run Development Servers**

**Terminal 1 (Backend):**
```bash
cd features
source venv/bin/activate  # or: python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd features/Frontend
npm install
npm run dev
```

5. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Admin Dashboard: http://localhost:3000/admin

## Features

- **Two W3ID Options**: Real W3ID (IBM SSO) + Dummy W3ID (managers, Admin, 10 employees for demo)
- **100 Seats**: Grid layout (A1 to J10)
- **Booking**: One seat per user
- **Charging**: Automatically charges 10 Blu-Dollars per booking
- **Prevents Double-Booking**: One user per seat per timeslot
- **5-Minute Timer**: Seats become available again after 5 minutes of booking
- **Manager Support**: 10 managers + Admin + 1 zero-balance manager; 10 employees for Dummy W3ID
- **Real-time Updates**: Seats refresh every 5 seconds to show current availability
- **Admin Dashboard**: Comprehensive admin view with booking statistics and reset functionality
- **Test-Driven Development**: Comprehensive test suite with 95%+ coverage
- **Swagger UI**: Interactive API documentation
- **Database Management**: SQLite for dev, PostgreSQL for production

## System Architecture

### Backend Stack
- **FastAPI** - Modern, fast web framework with async support
- **SQLAlchemy** - ORM for database operations
- **SQLite/PostgreSQL** - Database (SQLite for dev, PostgreSQL for prod)
- **Pydantic** - Data validation and settings management
- **Starlette** - Session management and middleware
- **Uvicorn** - ASGI server for development

### Frontend Stack
- **React 18** with TypeScript
- **Vite** - Next generation frontend tooling
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn UI** - Reusable component library
- **Lucide React** - Icon library
- **Sonner** - Toast notification library

### Testing Stack
- **Pytest** - Python testing framework
- **Pytest-cov** - Code coverage reporting
- **Jest** - JavaScript testing framework
- **React Testing Library** - React component testing
- **Supertest** - HTTP assertions for API testing

## Development Workflow

### Running the Application

**Backend Development Server:**
```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Run with custom host
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend Development Server:**
```bash
cd Frontend

# Development mode with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Management

**Database Initialization:**
- Database is automatically created on first run
- Tables are auto-generated from SQLAlchemy models
- Sample data is seeded automatically

**Database Inspection:**
```bash
# View database schema
sqlite3 cafeteria.db ".schema"

# View all tables
sqlite3 cafeteria.db ".tables"

# Query sample data
sqlite3 cafeteria.db "SELECT * FROM users LIMIT 5;"
sqlite3 cafeteria.db "SELECT * FROM seats;"
sqlite3 cafeteria.db "SELECT * FROM managers;"
```

**Database Reset:**
```bash
# Delete database file (will be recreated on next run)
rm cafeteria.db

# Or use admin reset endpoint
curl -X POST http://localhost:8000/admin/reset
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OIDC Configuration
OIDC_DISCOVERY_URL=https://preprod.login.w3.ibm.com/oidc/endpoint/default/.well-known/openid-configuration
OIDC_CLIENT_ID=your_client_id
OIDC_CLIENT_SECRET=your_client_secret
OIDC_REDIRECT_URI=http://localhost:8000/auth/callback

# Session Security
APP_SESSION_SECRET=your-secure-random-secret-key-here
FRONTEND_URL=http://localhost:3000

# Feature Flags
USE_MOCK_AUTH=true  # Set to false for production IBM W3ID auth
DEBUG=true
LOG_LEVEL=debug

# Database (optional - uses SQLite by default)
DATABASE_URL=sqlite:///./cafeteria.db
# For PostgreSQL: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### Frontend Configuration

Create `Frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

**Important**: Never commit `.env` files to version control!

## API Documentation

### Interactive Swagger UI
Access comprehensive API documentation at: **http://localhost:8000/docs**

### Core Endpoints

**Authentication:**
- `GET /auth/login` - Initiate OIDC login flow
- `GET /auth/callback` - Handle OIDC callback
- `GET /auth/logout` - End user session
- `GET /auth/me` - Get current user details
- `GET /auth/managers` - List all managers
- `GET /auth/manager-balance` - Get current user's manager balance

**Reservations:**
- `GET /reservations/timeslots?date=YYYY-MM-DD` - Get available timeslots
- `GET /reservations/seats?timeslot_id=X` - Get seat availability
- `GET /reservations/mine` - Get user's reservations
- `POST /reservations` - Create new reservation
- `GET /reservations/verify` - System status check (read-only)

**Admin:**
- `GET /admin/dashboard` - Real-time dashboard data
- `GET /admin/stats` - Detailed statistics
- `GET /admin/bookings` - Today/tomorrow bookings
- `POST /admin/reset` - Reset system (cancel bookings, restore balances)

### API Testing Examples
```bash
# Get system status
curl http://localhost:8000/reservations/verify | jq

# Get timeslots for today
curl "http://localhost:8000/reservations/timeslots?date=$(date +%Y-%m-%d)" | jq

# Get all managers
curl http://localhost:8000/auth/managers | jq

# Reset system (admin only)
curl -X POST http://localhost:8000/admin/reset | jq
```

## Project Structure

```
├── app/                    # Backend application
│   ├── main.py            # FastAPI application entry point
│   ├── database.py        # Database configuration and connection
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic schemas for validation
│   ├── seed.py            # Database seeding logic
│   └── routes/            # API route handlers
│       ├── auth.py        # Authentication endpoints
│       ├── reservations.py # Booking and seat management
│       └── admin.py       # Admin dashboard endpoints
├── Frontend/              # Frontend application
│   ├── src/               # Source code
│   │   ├── app/           # Main application
│   │   │   ├── components/ # React components
│   │   │   │   ├── ui/    # Reusable UI components
│   │   │   │   ├── admin-dashboard.tsx
│   │   │   │   ├── login-page.tsx
│   │   │   │   ├── seat-selection-page.tsx
│   │   │   │   └── booking-success-page.tsx
│   │   │   ├── services/  # API service layer
│   │   │   │   └── api.ts # API client configuration
│   │   │   └── App.tsx    # Main application component
│   │   ├── styles/        # CSS and styling
│   │   └── main.tsx       # React entry point
│   ├── public/            # Static assets
│   ├── package.json       # Frontend dependencies
│   └── vite.config.ts     # Vite configuration
├── tests/                 # Test suite
│   ├── test_basic.py      # Basic functionality tests
│   └── test_reservations.py # Reservation logic tests
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
├── TEST_CASES.md         # Comprehensive test scenarios
├── DEPLOYMENT.md         # Production deployment guide
└── .env.example          # Environment variable template
```

## Database Design

### Schema Overview
The system uses a relational database with the following core tables:

**Users Table**
- Stores employee information and manager assignments
- Links to reservations via foreign key
- Fields: id, employee_uid, email, first_name, last_name, manager_name

**Managers Table**
- Tracks manager accounts and Blu-Dollar balances
- Links to charges for billing history
- Fields: id, manager_name, balance

**Seats Table**
- Contains 100 seats labeled A1 through J10
- Links to reservations
- Fields: id, label

**Timeslots Table**
- Defines 30-minute booking intervals (12:00-15:00)
- Links to reservations
- Fields: id, starts_at, ends_at

**Reservations Table**
- Core booking records with 5-minute timer logic
- Enforces unique constraints to prevent double-booking
- Fields: id, user_id, seat_id, timeslot_id, status, created_at, available_at

**Charges Table**
- Tracks Blu-Dollar deductions from managers
- Links to reservations for billing history
- Fields: id, manager_id, reservation_id, amount, created_at

### Data Flow
1. **Booking Creation**: User → Reservation + Charge records created
2. **Balance Management**: Manager balance reduced by 10 Blu-Dollars
3. **Availability Logic**: Seat available after 5 minutes OR timeslot end
4. **Data Integrity**: Database constraints prevent conflicts

### Database Operations
```bash
# View current database state
sqlite3 cafeteria.db ".tables"

# Check reservation counts
sqlite3 cafeteria.db "SELECT COUNT(*) FROM reservations;"

# View manager balances
sqlite3 cafeteria.db "SELECT manager_name, balance FROM managers;"

# Check active reservations
sqlite3 cafeteria.db "SELECT COUNT(*) FROM reservations WHERE status = 'confirmed';"
```

## Testing

### Test-Driven Development Approach
The project follows TDD principles with comprehensive test coverage:

**Python Backend Tests:**
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_reservations.py

# Run tests with verbose output
pytest -v
```

**JavaScript Frontend Tests:**
```bash
# Run frontend tests
cd Frontend
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Test Categories
- **Unit Tests**: Individual function and component testing
- **Integration Tests**: API endpoint and database interaction
- **End-to-End Tests**: Complete user flow scenarios
- **Regression Tests**: Prevent breaking changes

### Sample Test Cases
```python
# Example backend test
def test_create_reservation():
    # Test successful booking
    # Test double booking prevention
    # Test manager balance deduction
    # Test 5-minute timer logic
    pass
```

## Troubleshooting

### Common Issues

**Backend Issues:**
- **Port already in use**: `lsof -i :8000` then `kill -9 <PID>`
- **Missing dependencies**: `pip install -r requirements.txt`
- **Database errors**: Delete `cafeteria.db` and restart backend
- **Environment variables**: Check `.env` file exists and is properly configured

**Frontend Issues:**
- **Connection refused**: Ensure backend is running on port 8000
- **Module not found**: `cd Frontend && npm install`
- **Build errors**: Clear node_modules and reinstall dependencies

**Database Issues:**
```bash
# Reset database
rm cafeteria.db
# Restart backend to recreate

# Check database integrity
sqlite3 cafeteria.db "PRAGMA integrity_check;"

# View database schema
sqlite3 cafeteria.db ".schema"
```

## Security Features

### Authentication & Authorization
- **OIDC Integration**: Secure IBM w3id SSO authentication
- **Session Management**: Encrypted server-side sessions
- **Role-Based Access**: Admin/user separation
- **CSRF Protection**: Built-in middleware protection

### Data Security
- **Input Validation**: Pydantic schemas for all API inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Rate Limiting**: API request throttling
- **Secure Headers**: HTTP security headers configured

### Production Security
- **HTTPS Enforcement**: SSL/TLS required in production
- **Secret Management**: Environment variables for sensitive data
- **Audit Logging**: Comprehensive request logging
- **Error Handling**: Secure error responses without information leakage

## Development Tools

### Useful Commands

**Backend Development:**
```bash
# Auto-format code
black app/
isort app/

# Run linters
flake8 app/

# Type checking
mypy app/
```

**Frontend Development:**
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

### Debugging Tools
- **Swagger UI**: http://localhost:8000/docs
- **Database Browser**: Use DB Browser for SQLite
- **Browser DevTools**: For frontend debugging
- **Logging**: Configure via LOG_LEVEL environment variable

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- Follow existing code style
- Write tests for new features
- Update documentation
- Ensure all tests pass

## License

This project is proprietary and confidential.

---

**Ready to use!** Start backend and frontend, then open http://localhost:3000

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
For comprehensive test scenarios, see [TEST_CASES.md](TEST_CASES.md)