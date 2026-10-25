from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, Response, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, Text, UniqueConstraint, and_, create_engine, func, insert, select
from werkzeug.security import check_password_hash, generate_password_hash

metadata = MetaData()
users = Table('platform_users', metadata,
    Column('id', Integer, primary_key=True), Column('project', String(80), nullable=False),
    Column('email', String(255), nullable=False), Column('password_hash', Text, nullable=False),
    Column('role', String(20), nullable=False, default='user'), Column('created_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint('project', 'email', name='uq_platform_user_project_email'))
api_keys = Table('platform_api_keys', metadata,
    Column('id', Integer, primary_key=True), Column('project', String(80), nullable=False), Column('user_id', Integer, nullable=False),
    Column('label', String(80), nullable=False), Column('key_hash', String(64), nullable=False, unique=True),
    Column('created_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)))
events = Table('platform_events', metadata,
    Column('id', Integer, primary_key=True), Column('project', String(80), nullable=False), Column('event_type', String(120), nullable=False),
    Column('actor', String(255), nullable=False, default='anonymous'), Column('payload_json', Text, nullable=False, default='{}'),
    Column('created_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)))
models = Table('platform_models', metadata,
    Column('id', Integer, primary_key=True), Column('project', String(80), nullable=False), Column('name', String(120), nullable=False),
    Column('version', String(64), nullable=False), Column('stage', String(32), nullable=False, default='candidate'),
    Column('metrics_json', Text, nullable=False, default='{}'), Column('created_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint('project', 'name', 'version', name='uq_platform_model_version'))
experiments = Table('platform_experiments', metadata,
    Column('id', Integer, primary_key=True), Column('project', String(80), nullable=False), Column('name', String(120), nullable=False),
    Column('params_json', Text, nullable=False, default='{}'), Column('metrics_json', Text, nullable=False, default='{}'),
    Column('created_at', DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)))


def _database_url():
    url = os.getenv('DATABASE_URL', 'sqlite:///instance/platform.db')
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg://' + url[len('postgres://'):]
    elif url.startswith('postgresql://') and '+psycopg' not in url:
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    if url.startswith('sqlite:///'):
        os.makedirs('instance', exist_ok=True)
    return url


def init_platform(app, project_name: str):
    app.secret_key = os.getenv('SECRET_KEY', app.secret_key or 'dev-only-change-me')
    url = _database_url()
    kwargs = {'pool_pre_ping': True}
    if url.startswith('sqlite:'):
        kwargs['connect_args'] = {'check_same_thread': False}
    engine = create_engine(url, **kwargs)
    metadata.create_all(engine)
    serializer = URLSafeTimedSerializer(app.secret_key, salt=f'{project_name}-auth')
    bp = Blueprint(f'platform_{project_name.replace("-", "_")}', __name__)
    app.extensions['portfolio_platform'] = {'engine': engine, 'project': project_name}

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        if os.getenv('SENTRY_DSN'):
            sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()], traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')))
    except Exception:
        pass

    logger = logging.getLogger(project_name)
    if not logger.handlers:
        logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'), format='%(message)s')

    windows = defaultdict(deque)
    lock = threading.Lock()
    metrics = {'requests': 0, 'errors': 0}
    limit = int(os.getenv('RATE_LIMIT_PER_MINUTE', '120'))

    def record(event_type: str, payload=None, actor='anonymous'):
        try:
            with engine.begin() as conn:
                conn.execute(insert(events).values(project=project_name, event_type=event_type, actor=actor, payload_json=json.dumps(payload or {}, default=str)))
        except Exception:
            logger.exception('platform_event_write_failed')

    def identity():
        cached = getattr(g, 'platform_identity', None)
        if cached:
            return cached
        auth = request.headers.get('Authorization', '')
        token = auth[7:].strip() if auth.startswith('Bearer ') else ''
        if token:
            try:
                data = serializer.loads(token, max_age=7 * 24 * 3600)
                if data.get('project') == project_name:
                    g.platform_identity = data
                    return data
            except (BadSignature, SignatureExpired):
                pass
        raw_key = request.headers.get('X-API-Key', '')
        if raw_key:
            digest = hashlib.sha256(raw_key.encode()).hexdigest()
            with engine.begin() as conn:
                row = conn.execute(select(api_keys.c.user_id, users.c.email, users.c.role).join(users, users.c.id == api_keys.c.user_id).where(and_(api_keys.c.project == project_name, api_keys.c.key_hash == digest))).mappings().first()
            if row:
                data = {'user_id': row['user_id'], 'email': row['email'], 'role': row['role'], 'project': project_name}
                g.platform_identity = data
                return data
        return None

    def require_auth(role=None):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                who = identity()
                if not who:
                    return jsonify({'error': 'authentication required'}), 401
                if role and who.get('role') != role:
                    return jsonify({'error': 'insufficient role'}), 403
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    @app.before_request
    def _platform_before_request():
        g.request_started = time.perf_counter()
        if request.path.startswith('/api/'):
            now = time.time()
            key = f'{request.remote_addr}:{request.path}'
            with lock:
                q = windows[key]
                while q and now - q[0] > 60:
                    q.popleft()
                if len(q) >= limit:
                    return jsonify({'error': 'rate limit exceeded', 'retry_after_seconds': 60}), 429
                q.append(now)

    @app.after_request
    def _platform_after_request(response):
        metrics['requests'] += 1
        if response.status_code >= 500:
            metrics['errors'] += 1
        elapsed = round((time.perf_counter() - getattr(g, 'request_started', time.perf_counter())) * 1000, 2)
        req_id = request.headers.get('X-Request-ID') or secrets.token_hex(8)
        response.headers['X-Request-ID'] = req_id
        logger.info(json.dumps({'project': project_name, 'method': request.method, 'path': request.path, 'status': response.status_code, 'latency_ms': elapsed, 'request_id': req_id}))
        if request.path.startswith('/api/') and request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            who = getattr(g, 'platform_identity', None) or {}
            record(f'http:{request.method}:{request.path}', {'status': response.status_code, 'request_id': req_id}, who.get('email', 'anonymous'))
        return response

    @app.errorhandler(500)
    def _platform_error(_):
        metrics['errors'] += 1
        return jsonify({'error': 'internal server error'}), 500

    @bp.get('/api/platform/status')
    def status():
        return jsonify({'project': project_name, 'storage': engine.dialect.name, 'auth': True, 'rate_limit_per_minute': limit})

    @bp.post('/api/auth/register')
    def register():
        payload = request.get_json(silent=True) or {}
        email = str(payload.get('email', '')).strip().lower()
        password = str(payload.get('password', ''))
        if '@' not in email or len(password) < 8:
            return jsonify({'error': 'valid email and password of at least 8 characters required'}), 400
        with engine.begin() as conn:
            exists = conn.execute(select(users.c.id).where(and_(users.c.project == project_name, users.c.email == email))).first()
            if exists:
                return jsonify({'error': 'account already exists'}), 409
            count = conn.execute(select(func.count()).select_from(users).where(users.c.project == project_name)).scalar_one()
            role = 'admin' if count == 0 else 'user'
            result = conn.execute(insert(users).values(project=project_name, email=email, password_hash=generate_password_hash(password), role=role))
            user_id = result.inserted_primary_key[0]
        token = serializer.dumps({'user_id': user_id, 'email': email, 'role': role, 'project': project_name})
        record('auth.register', {'role': role}, email)
        return jsonify({'token': token, 'role': role, 'email': email})

    @bp.post('/api/auth/login')
    def login():
        payload = request.get_json(silent=True) or {}
        email = str(payload.get('email', '')).strip().lower()
        password = str(payload.get('password', ''))
        with engine.begin() as conn:
            row = conn.execute(select(users).where(and_(users.c.project == project_name, users.c.email == email))).mappings().first()
        if not row or not check_password_hash(row['password_hash'], password):
            return jsonify({'error': 'invalid credentials'}), 401
        token = serializer.dumps({'user_id': row['id'], 'email': row['email'], 'role': row['role'], 'project': project_name})
        record('auth.login', {}, email)
        return jsonify({'token': token, 'role': row['role'], 'email': row['email']})

    @bp.get('/api/auth/me')
    @require_auth()
    def me():
        return jsonify(identity())

    @bp.post('/api/auth/api-key')
    @require_auth()
    def issue_api_key():
        who = identity()
        raw = 'pk_' + secrets.token_urlsafe(32)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        label = str((request.get_json(silent=True) or {}).get('label', 'default'))[:80]
        with engine.begin() as conn:
            conn.execute(insert(api_keys).values(project=project_name, user_id=who['user_id'], label=label, key_hash=digest))
        return jsonify({'api_key': raw, 'label': label})

    @bp.route('/api/platform/models', methods=['GET', 'POST'])
    @require_auth()
    def model_registry():
        if request.method == 'GET':
            with engine.begin() as conn:
                rows = conn.execute(select(models).where(models.c.project == project_name).order_by(models.c.created_at.desc())).mappings().all()
            return jsonify([{**dict(r), 'created_at': str(r['created_at'])} for r in rows])
        payload = request.get_json(silent=True) or {}
        if not payload.get('name') or not payload.get('version'):
            return jsonify({'error': 'name and version are required'}), 400
        with engine.begin() as conn:
            conn.execute(insert(models).values(project=project_name, name=str(payload['name']), version=str(payload['version']), stage=str(payload.get('stage', 'candidate')), metrics_json=json.dumps(payload.get('metrics', {}))))
        record('model.registered', payload, identity()['email'])
        return jsonify({'saved': True}), 201

    @bp.route('/api/platform/experiments', methods=['GET', 'POST'])
    @require_auth()
    def experiment_registry():
        if request.method == 'GET':
            with engine.begin() as conn:
                rows = conn.execute(select(experiments).where(experiments.c.project == project_name).order_by(experiments.c.created_at.desc()).limit(100)).mappings().all()
            return jsonify([{**dict(r), 'created_at': str(r['created_at'])} for r in rows])
        payload = request.get_json(silent=True) or {}
        with engine.begin() as conn:
            conn.execute(insert(experiments).values(project=project_name, name=str(payload.get('name', 'experiment')), params_json=json.dumps(payload.get('params', {})), metrics_json=json.dumps(payload.get('metrics', {}))))
        return jsonify({'saved': True}), 201

    @bp.get('/api/admin/overview')
    @require_auth('admin')
    def admin_overview():
        with engine.begin() as conn:
            u = conn.execute(select(func.count()).select_from(users).where(users.c.project == project_name)).scalar_one()
            e = conn.execute(select(func.count()).select_from(events).where(events.c.project == project_name)).scalar_one()
            m = conn.execute(select(func.count()).select_from(models).where(models.c.project == project_name)).scalar_one()
            x = conn.execute(select(func.count()).select_from(experiments).where(experiments.c.project == project_name)).scalar_one()
        return jsonify({'users': u, 'events': e, 'models': m, 'experiments': x})

    @bp.get('/api/admin/export/events.csv')
    @require_auth('admin')
    def export_events():
        with engine.begin() as conn:
            rows = conn.execute(select(events).where(events.c.project == project_name).order_by(events.c.created_at.desc()).limit(2000)).mappings().all()
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(['id', 'event_type', 'actor', 'payload_json', 'created_at'])
        for r in rows:
            writer.writerow([r['id'], r['event_type'], r['actor'], r['payload_json'], r['created_at']])
        return Response(out.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={project_name}-events.csv'})

    @bp.get('/metrics')
    def prometheus_metrics():
        body = f'portfolio_requests_total{{project="{project_name}"}} {metrics["requests"]}\nportfolio_errors_total{{project="{project_name}"}} {metrics["errors"]}\n'
        return Response(body, mimetype='text/plain')

    app.register_blueprint(bp)
    return engine
