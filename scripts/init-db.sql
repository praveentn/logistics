-- Initialize databases for all microservices

-- Create databases
CREATE DATABASE orders_db;
CREATE DATABASE tracking_db;
CREATE DATABASE inventory_db;
CREATE DATABASE notifications_db;

-- Connect to each database and add extensions
\c orders_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c tracking_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c inventory_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c notifications_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
