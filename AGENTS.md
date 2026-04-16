# AGENTS.md

## Project overview
PDF QUICK is a Flask web app for PDF utilities such as merge, split, compress, Office/image conversion, security tools, and Groq-powered AI processing.

## Architecture
- `main.py`: Flask app, routes, and HTTP responses.
- `controllers/`: feature-specific business logic.
- `templates/`: Jinja HTML views.
- `static/`: CSS and SEO assets.
- `utils/`: shared helpers.

## Working rules
- Keep route handlers thin and move heavy logic into controllers.
- Preserve the current privacy-first behavior and in-memory file processing with `io.BytesIO` where possible.
- Avoid introducing unnecessary dependencies or background services.
- Prefer small, targeted fixes over broad rewrites.
- Keep user-facing copy primarily in Spanish unless the feature already uses English.

## AI and secrets
- AI features depend on the `GROQ_API_KEY` environment variable.
- Handle missing keys with clear, user-safe errors.

## Local validation
- Install dependencies with `pip install -r requirements.txt`.
- Run locally with `python3 main.py` if the file is used directly, or `flask --app main run` for development.
- For basic validation, use `python3 -m compileall .` after Python changes.

## Agent expectations
When making changes:
1. Understand the affected controller and route flow first.
2. Make the minimal root-cause fix.
3. Verify with a fresh syntax or runtime check before declaring success.
4. Do not claim tests or builds passed unless they were actually run.
