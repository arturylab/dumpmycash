#!/usr/bin/env python3
from app import create_app
from flask_migrate import Migrate
from app.models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    import sys
    if 'db' not in sys.argv:
        app.run(debug=True)

