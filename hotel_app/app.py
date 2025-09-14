from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Подключение к базе данных
def get_db_connection():
    conn = psycopg2.connect(
        host="db",  # имя сервиса в docker-compose
        database="hotel_simple",
        user="postgres",
        password="password"
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# API: Получить все номера
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM rooms ORDER BY number;')
    rooms = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rooms)

# API: Поиск свободных номеров
@app.route('/api/rooms/available', methods=['GET'])
def get_available_rooms():
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = """
    SELECT * FROM rooms 
    WHERE id NOT IN (
        SELECT room_id FROM bookings 
        WHERE status = 'подтверждено'
        AND (check_in_date <= %s AND check_out_date >= %s)
    )
    ORDER BY number;
    """
    
    cur.execute(query, (check_out, check_in))
    rooms = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify(rooms)

# API: Создать бронирование
@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Добавляем гостя
        cur.execute(
            'INSERT INTO guests (full_name, phone) VALUES (%s, %s) RETURNING id;',
            (data['guest_name'], data['guest_phone'])
        )
        guest_id = cur.fetchone()[0]
        
        # Рассчитываем стоимость
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d')
        nights = (check_out - check_in).days
        
        cur.execute('SELECT price_per_night FROM rooms WHERE id = %s;', (data['room_id'],))
        price_per_night = cur.fetchone()[0]
        
        total_price = nights * price_per_night
        
        # Добавляем детскую кровать если нужно
        if data.get('child_bed'):
            total_price += 500  # цена детской кровати
        
        # Создаем бронирование
        cur.execute(
            '''INSERT INTO bookings 
            (guest_id, room_id, check_in_date, check_out_date, adults_count, children_count, total_price) 
            VALUES (%s, %s, %s, %s, %s, %s, %s);''',
            (guest_id, data['room_id'], data['check_in'], data['check_out'], 
             data['adults'], data.get('children', 0), total_price)
        )
        
        # Обновляем статус номера
        cur.execute(
            'UPDATE rooms SET status = %s WHERE id = %s;',
            ('забронирован', data['room_id'])
        )
        
        conn.commit()
        
        return jsonify({'message': 'Бронь успешно создана!'}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
        
    finally:
        cur.close()
        conn.close()

# API: Получить все бронирования
@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
    SELECT b.*, g.full_name, g.phone, r.number as room_number 
    FROM bookings b
    JOIN guests g ON b.guest_id = g.id
    JOIN rooms r ON b.room_id = r.id
    ORDER BY b.created_at DESC;
    ''')
    
    bookings = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify(bookings)

# API: Отменить бронирование
@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Получаем room_id перед удалением
        cur.execute('SELECT room_id FROM bookings WHERE id = %s;', (booking_id,))
        room_id = cur.fetchone()[0]
        
        # Отменяем бронирование
        cur.execute(
            'UPDATE bookings SET status = %s WHERE id = %s;',
            ('отменено', booking_id)
        )
        
        # Освобождаем номер
        cur.execute(
            'UPDATE rooms SET status = %s WHERE id = %s;',
            ('свободен', room_id)
        )
        
        conn.commit()
        return jsonify({'message': 'Бронь успешно отменена!'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
        
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)