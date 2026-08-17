-- Creates Airflow metadata database/user on first Postgres init.
-- For an existing volume, apply manually (see README).

CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
