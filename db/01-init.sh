#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -v app_pw="$APP_DB_PASSWORD" -v monitor_pw="$MONITOR_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE clinic_app LOGIN PASSWORD %L', :'app_pw') \gexec
SELECT format('CREATE ROLE clinic_monitor LOGIN PASSWORD %L', :'monitor_pw') \gexec
GRANT pg_monitor TO clinic_monitor;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','reception')));
CREATE TABLE patients (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, phone VARCHAR(15) NOT NULL UNIQUE, birth_date DATE NOT NULL);
CREATE TABLE doctors (id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, specialty VARCHAR(100) NOT NULL);
CREATE TABLE appointments (id SERIAL PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id), doctor_id INTEGER NOT NULL REFERENCES doctors(id), starts_at TIMESTAMP NOT NULL, status TEXT NOT NULL CHECK(status IN ('booked','completed','cancelled')));
CREATE UNIQUE INDEX doctor_slot ON appointments(doctor_id,starts_at) WHERE status != 'cancelled';
CREATE UNIQUE INDEX patient_slot ON appointments(patient_id,starts_at) WHERE status != 'cancelled';
GRANT CONNECT ON DATABASE clinic TO clinic_app,clinic_monitor;
GRANT USAGE ON SCHEMA public TO clinic_app,clinic_monitor;
GRANT SELECT,INSERT,UPDATE,DELETE ON patients,doctors,appointments TO clinic_app;
GRANT SELECT,INSERT ON users TO clinic_app;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO clinic_app;
SQL
