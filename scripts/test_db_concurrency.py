"""Run via docker compose exec -T webapp python < scripts/test_db_concurrency.py."""
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from server import engine

barrier=Barrier(2)
with engine.begin() as c:
    pid=c.execute(text('INSERT INTO patients(name,phone,birth_date) VALUES(:n,:p,:b) RETURNING id'),
        {'n':'Concurrency demo','p':'08'+str(secrets.randbelow(10**8)).zfill(8),'b':'2000-01-01'}).scalar_one()
    did=c.execute(text("INSERT INTO doctors(name,specialty) VALUES('Concurrency demo','Test') RETURNING id")).scalar_one()
def book(_):
    barrier.wait(timeout=10)
    try:
        with engine.begin() as c:
            c.execute(text("INSERT INTO appointments(patient_id,doctor_id,starts_at,status) VALUES(:p,:d,:s,'booked')"),
                {'p':pid,'d':did,'s':(datetime.now()+timedelta(days=5)).replace(hour=9,minute=0,second=0,microsecond=0)})
        return 'success'
    except IntegrityError:
        return 'conflict'
try:
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(book,range(2)))
    assert sorted(results)==['conflict','success'], results
    print('PASS PostgreSQL concurrent booking: one success, one conflict')
finally:
    with engine.begin() as c:
        c.execute(text('DELETE FROM appointments WHERE doctor_id=:d'),{'d':did})
        c.execute(text('DELETE FROM patients WHERE id=:p'),{'p':pid})
        c.execute(text('DELETE FROM doctors WHERE id=:d'),{'d':did})
