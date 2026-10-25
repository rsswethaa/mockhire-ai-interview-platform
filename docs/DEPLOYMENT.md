# Setup and Deployment

## Local
```bash
git clone https://github.com/rsswethaa/mockhire-ai-interview-platform.git
cd mockhire-ai-interview-platform
python demo.py
python -m unittest discover -s tests -v
```

Optional local database:
```bash
python -c "from src.storage import init_db; init_db('mockhire.db', seed=True)"
```

## Production-shaped architecture
A serious deployment would separate web/API, evaluation service and managed database layers; use authentication, HTTPS, encrypted storage, background jobs, observability and role-based access.

The repository intentionally avoids pretending that an academic portfolio prototype is production hiring infrastructure.
