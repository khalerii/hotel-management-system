-- Создание таблиц
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    number VARCHAR(10) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('стандарт', 'комфорт', 'люкс')),
    capacity INTEGER NOT NULL,
    price_per_night DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'свободен' CHECK (status IN ('свободен', 'забронирован', 'занят'))
);

CREATE TABLE guests (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    guest_id INTEGER REFERENCES guests(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    adults_count INTEGER NOT NULL,
    children_count INTEGER DEFAULT 0,
    total_price DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'подтверждено' CHECK (status IN ('подтверждено', 'отменено', 'завершено')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL
);

CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE booking_services (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES services(id) ON DELETE CASCADE
);

-- Добавляем тестовые данные
INSERT INTO rooms (number, category, capacity, price_per_night) VALUES
('101', 'стандарт', 2, 2500),
('102', 'стандарт', 2, 2500),
('201', 'комфорт', 3, 3500),
('202', 'комфорт', 3, 3500),
('301', 'люкс', 2, 5000);

INSERT INTO services (name, price) VALUES
('детская кровать', 500);

INSERT INTO users (username, password_hash, full_name) VALUES
('admin', '$2b$10$r4B2B7Hj6U6Z6Z6Z6Z6Z6e6Z6Z6Z6Z6Z6Z6Z6Z6Z6Z6Z6Z6Z6Z6', 'Иванов Иван Иванович');
