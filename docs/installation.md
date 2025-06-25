# Installation & Setup

## Prerequisites

- Python 3.8+
- pip package manager
- SQLite (default) or PostgreSQL

## Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd DumpMyCash
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   python manage.py db init
   python manage.py db migrate
   python manage.py db upgrade
   ```

6. **Run Application**
   ```bash
   python run.py
   ```

## Environment Variables

- `FLASK_ENV`: Development or production
- `SECRET_KEY`: Application secret key
- `DATABASE_URL`: Database connection string

## Database Migration

```bash
# Create migration
python manage.py db migrate -m "Description"

# Apply migration
python manage.py db upgrade
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```
