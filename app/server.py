import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from functools import wraps
from logging.handlers import RotatingFileHandler

import click
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ['SECRET_KEY'], SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=False,
                  PERMANENT_SESSION_LIFETIME=timedelta(hours=4), MAX_CONTENT_LENGTH=16384)
CSRFProtect(app)
db_url = os.getenv('DATABASE_URL') or URL.create('postgresql+psycopg', username='clinic_app',
    password=os.environ['APP_DB_PASSWORD'], host='db', database='clinic')
engine = create_engine(db_url, pool_pre_ping=True)
logger = logging.getLogger('clinic')
logger.setLevel(logging.INFO)
logdir = os.getenv('LOG_DIR', '/logs/webapp')
os.makedirs(logdir, exist_ok=True)
handler = RotatingFileHandler(logdir + '/app.log', maxBytes=2_000_000, backupCount=3)
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())
requests = Counter('clinic_http_requests_total', 'HTTP requests', ['method', 'endpoint', 'status'])
latency = Histogram('clinic_http_request_seconds', 'Request latency', ['endpoint'])

@app.template_filter('clinic_datetime')
def clinic_datetime(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime('%d/%m/%Y · %H:%M')

def event(level, name, **values):
    logger.log(getattr(logging, level), json.dumps(dict(level=level, event=name, **values)))

def rows(query, **params):
    with engine.connect() as c:
        return c.execute(text(query), params).mappings().all()

def staff(admin=False):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            if admin and g.user['role'] != 'admin':
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator

@app.before_request
def before():
    g.started = time.monotonic()
    g.user = None
    if session.get('uid'):
        found = rows('SELECT id, username, role FROM users WHERE id=:id', id=session['uid'])
        g.user = found[0] if found else None

@app.after_request
def after(response):
    endpoint = request.endpoint or 'not_found'
    if endpoint != 'metrics':
        requests.labels(request.method, endpoint, str(response.status_code)).inc()
        latency.labels(endpoint).observe(time.monotonic()-getattr(g, 'started', time.monotonic()))
        # Deliberately exclude request bodies, names, phone numbers and query strings.
        event('ERROR' if response.status_code >= 500 else 'INFO', 'http_request',
              endpoint=endpoint, method=request.method, status=response.status_code)
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/healthz')
def health():
    try:
        rows('SELECT 1')
        return {'status': 'ok', 'database': 'connected'}
    except Exception:
        return {'status': 'unhealthy'}, 503

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = rows('SELECT * FROM users WHERE username=:u', u=request.form.get('username', ''))
        if user and check_password_hash(user[0]['password_hash'], request.form.get('password', '')):
            session.clear()
            session['uid'] = user[0]['id']
            session.permanent = True
            event('INFO', 'login_success', user_id=user[0]['id'])
            return redirect(url_for('index'))
        event('WARNING', 'login_failed')
        flash('Sai tên đăng nhập hoặc mật khẩu.', 'error')
    return render_template('login.html')

@app.post('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@staff()
def index():
    return render_template('index.html',
        patients=rows('SELECT * FROM patients ORDER BY id DESC'),
        doctors=rows('SELECT * FROM doctors ORDER BY id'),
        appointments=rows('''SELECT a.*, p.name AS patient, d.name AS doctor FROM appointments a
          JOIN patients p ON a.patient_id=p.id JOIN doctors d ON a.doctor_id=d.id
          ORDER BY a.starts_at DESC'''))

def field(name, maxlen=100):
    value = request.form.get(name, '').strip()
    if not value or len(value) > maxlen:
        raise ValueError('Thông tin bắt buộc còn thiếu hoặc quá dài.')
    return value

@app.post('/patients/save')
@staff()
def save_patient():
    try:
        name, phone = field('name'), field('phone', 15)
        if not phone.isdigit() or not 9 <= len(phone) <= 15:
            raise ValueError('Số điện thoại cần 9–15 chữ số.')
        birth = datetime.strptime(field('birth_date'), '%Y-%m-%d').date()
        if birth > datetime.now().date():
            raise ValueError('Ngày sinh không được ở tương lai.')
        values = dict(name=name, phone=phone, birth_date=birth)
        with engine.begin() as c:
            if request.form.get('id'):
                values['id'] = int(request.form['id'])
                c.execute(text('UPDATE patients SET name=:name, phone=:phone, birth_date=:birth_date WHERE id=:id'), values)
            else:
                c.execute(text('INSERT INTO patients(name,phone,birth_date) VALUES(:name,:phone,:birth_date)'), values)
        event('INFO', 'patient_saved', actor=g.user['id'])
        flash('Đã lưu bệnh nhân.')
    except (ValueError, IntegrityError):
        flash('Kiểm tra tên, ngày sinh và số điện thoại; số điện thoại không được trùng.', 'error')
    return redirect(url_for('index'))

@app.post('/patients/<int:pid>/delete')
@staff(admin=True)
def delete_patient(pid):
    try:
        with engine.begin() as c:
            c.execute(text('DELETE FROM patients WHERE id=:id'), {'id': pid})
        event('INFO', 'patient_deleted', actor=g.user['id'])
        flash('Đã xóa bệnh nhân.')
    except IntegrityError:
        flash('Bệnh nhân đã có lịch khám; không xóa để giữ lịch sử.', 'error')
    return redirect(url_for('index'))

@app.post('/doctors')
@staff(admin=True)
def add_doctor():
    try:
        values = dict(name=field('name'), specialty=field('specialty'))
        with engine.begin() as c:
            c.execute(text('INSERT INTO doctors(name,specialty) VALUES(:name,:specialty)'), values)
        flash('Đã thêm bác sĩ.')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))

@app.post('/appointments')
@staff()
def book():
    try:
        at = datetime.strptime(field('starts_at'), '%Y-%m-%dT%H:%M')
        if at <= datetime.now() or at.minute not in (0, 30) or not 8 <= at.hour < 17:
            raise ValueError('Chọn giờ tương lai, từ 08:00 đến 16:30, mỗi ca 30 phút.')
        values = dict(patient=int(field('patient_id')), doctor=int(field('doctor_id')), at=at)
        with engine.begin() as c:
            c.execute(text('INSERT INTO appointments(patient_id,doctor_id,starts_at,status) VALUES(:patient,:doctor,:at,\'booked\')'), values)
        event('INFO', 'appointment_booked', actor=g.user['id'])
        flash('Đặt lịch thành công.')
    except IntegrityError:
        event('WARNING', 'appointment_conflict')
        flash('Bác sĩ hoặc bệnh nhân đã có lịch trong ca này, hoặc dữ liệu không tồn tại.', 'error')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))

@app.post('/appointments/<int:aid>/status')
@staff()
def status(aid):
    value = request.form.get('status')
    if value not in ('completed', 'cancelled'):
        abort(400)
    with engine.begin() as c:
        c.execute(text('UPDATE appointments SET status=:s WHERE id=:id AND status=\'booked\''), {'s':value, 'id':aid})
    event('INFO', 'appointment_status_changed', actor=g.user['id'], status=value)
    return redirect(url_for('index'))

@app.post('/demo-error')
@staff(admin=True)
def demo_error():
    if os.getenv('ENABLE_DEMO') != 'true':
        abort(404)
    event('ERROR', 'controlled_demo_error')
    return 'Lỗi 503 giả lập để kiểm tra giám sát và LogQL.', 503

@app.cli.command('seed')
def seed():
    """Create initial accounts and fictional records, safe to repeat."""
    with engine.begin() as c:
        for username, role, env in [('admin','admin','ADMIN_PASSWORD'), ('letan','reception','RECEPTION_PASSWORD')]:
            password = os.environ[env]
            if len(password) < 12:
                raise click.ClickException('Mật khẩu cần ít nhất 12 ký tự.')
            c.execute(text('INSERT INTO users(username,password_hash,role) VALUES(:u,:p,:r) ON CONFLICT(username) DO NOTHING'),
                      {'u':username,'p':generate_password_hash(password),'r':role})
        if not c.execute(text('SELECT 1 FROM doctors LIMIT 1')).first():
            for name, specialty in [('BS Minh An (demo)','Nội tổng quát'),('BS Lan Anh (demo)','Nhi khoa')]:
                c.execute(text('INSERT INTO doctors(name,specialty) VALUES(:n,:s)'), {'n':name,'s':specialty})
        if not c.execute(text('SELECT 1 FROM patients LIMIT 1')).first():
            c.execute(text("INSERT INTO patients(name,phone,birth_date) VALUES('Bệnh nhân mẫu A','0900000001','2000-01-01')"))
    click.echo('Seed hoàn tất. Tài khoản: admin / letan. Mật khẩu lấy trong .env.')
