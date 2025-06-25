# DumpMyCash

> Minimalist personal financial management web application

DumpMyCash is a simple, clean, and efficient tool for tracking personal finances. Built with Flask and following minimalist design principles, it provides essential financial management features without unnecessary complexity.

## ✨ Features

- **Account Management**: Multiple accounts with color-coded identification
- **Transaction Tracking**: Income and expense recording with categories
- **Smart Categories**: Organize transactions with custom categories and emojis
- **Real-time Balance**: Automatic balance calculation and updates
- **Transfer System**: Move money between accounts seamlessly
- **Responsive Design**: Works on desktop and mobile devices
- **Secure Authentication**: Session-based user authentication

## 🚀 Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd DumpMyCash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize Database**
   ```bash
   python manage.py db init
   python manage.py db migrate
   python manage.py db upgrade
   ```

4. **Run Application**
   ```bash
   python run.py
   ```

Visit `http://localhost:5000` to start managing your finances.

## 📖 Documentation

- [Installation & Setup](docs/installation.md) - Complete installation guide
- [Dashboard](docs/dashboard.md) - Financial overview and quick actions
- [Account Management](docs/account.md) - Managing financial accounts
- [Transactions](docs/transactions.md) - Recording and tracking money flow
- [Categories](docs/categories.md) - Organizing transactions
- [Profile](docs/profile.md) - User settings and data management
- [Help System](docs/help.md) - User guidance and support
- [API Reference](docs/api.md) - Technical API documentation

## 🏗️ Tech Stack

- **Backend**: Flask 3.1.1, SQLAlchemy, Flask-Migrate
- **Frontend**: Bootstrap 5.3.6, JavaScript ES6
- **Database**: SQLite (default), PostgreSQL supported
- **Authentication**: Flask-Login, WTForms with CSRF protection
- **Testing**: Pytest with coverage

## 📁 Project Structure

```
DumpMyCash/
├── app/                    # Application package
│   ├── static/            # CSS, JS, images
│   ├── templates/         # Jinja2 templates
│   ├── __init__.py       # App factory
│   ├── models.py         # Database models
│   ├── auth.py           # Authentication routes
│   ├── account.py        # Account management
│   ├── transactions.py   # Transaction handling
│   ├── categories.py     # Category management
│   ├── home.py           # Dashboard logic
│   └── profile.py        # User profile
├── tests/                 # Test suite
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
├── run.py                # Application entry point
└── manage.py             # Database management
```

## 🎯 Philosophy

DumpMyCash follows minimalist principles:

- **Essential Features Only**: No bloated functionality
- **Clean Interface**: Simple, intuitive user experience
- **Fast Performance**: Lightweight and responsive
- **Easy Setup**: Quick installation and configuration
- **Privacy First**: Local data storage, no external services

## 🧪 Beta Status

This application is currently in beta phase. Your feedback is valuable for improving the experience.

**Found a bug or have suggestions?**  
Contact: [arturylab@gmail.com](mailto:arturylab@gmail.com?subject=DumpMyCash%20Beta%20Feedback)

## 🔒 Security

- Session-based authentication
- CSRF protection on all forms
- Password hashing with Werkzeug
- Input validation and sanitization

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test module
pytest tests/test_transactions.py
```

## 📜 License

This project is open source. See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

---

**DumpMyCash** - Simple. Clean. Effective.  
*Personal financial management made minimalist.*
