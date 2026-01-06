# TODO List for URL Shortening Service

- [x] Set up Python virtual environment and install dependencies (Flask, SQLAlchemy)
- [x] Create project structure: app.py, models.py, utils.py, templates/index.html, requirements.txt
- [x] Implement database model in models.py (URL model with original_url, short_code, clicks, created_at)
- [x] Implement short code generation in utils.py (Base62 encoding)
- [x] Implement API routes in app.py (POST /shorten, GET /<shortcode>, GET /stats/<shortcode>)
- [x] Create simple HTML frontend in templates/index.html
- [x] Test the app locally
- [x] Prepare for Render deployment (add runtime.txt if needed)
