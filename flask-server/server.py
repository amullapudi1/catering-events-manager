from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import text
import os

app = Flask(__name__, static_folder='../client/build', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catering.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)

class Event(db.Model):
    __tablename__ = 'event'
    event_id = db.Column(db.Integer, primary_key=True)
    event_date = db.Column(db.String(10), nullable=False, index=True)
    start = db.Column(db.String(5), nullable=False)
    end = db.Column(db.String(5), nullable=False)
    guest_count = db.Column(db.Integer, nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.menu_id'), nullable=True, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.location_id'), nullable=True, index=True)

    menu = db.relationship('Menu', backref=db.backref('events', lazy=True))
    location = db.relationship('Location', backref=db.backref('events', lazy=True))

class Menu(db.Model):
    menu_id = db.Column(db.Integer, primary_key=True)
    menu_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Float, nullable=False)

class Location(db.Model):
    location_id = db.Column(db.Integer, primary_key=True)
    venue = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(50), nullable=True)
    capacity = db.Column(db.Integer, nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    return jsonify([{
        'event_id': event.event_id,
        'event_date': event.event_date,
        'start': event.start,
        'end': event.end,
        'guest_count': event.guest_count,
        'menu_id': event.menu_id,
        'menu_name': event.menu.menu_name if event.menu else None,
        'location_id': event.location_id,
        'location_venue': event.location.venue if event.location else None
    } for event in events])

@app.route('/events', methods=['POST'])
def create_event():
    data = request.json
    db.session.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
    with db.session.begin():
        new_event = Event(
            event_date=data['event_date'],
            start=data['start'],
            end=data['end'],
            guest_count=int(data['guest_count']),
            menu_id=int(data['menu_id']),
            location_id=int(data['location_id'])
        )
        db.session.add(new_event)
    return jsonify({'message': 'event created'}), 201

@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json
    db.session.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
    with db.session.begin():
        event = Event.query.get(event_id)
        if event:
            event.event_date = data['event_date']
            event.start = data['start']
            event.end = data['end']
            event.guest_count = int(data['guest_count'])
            event.menu_id = int(data['menu_id'])
            event.location_id = int(data['location_id'])
        else:
            return jsonify({'message': 'event not found'}), 404
    return jsonify({'message': 'event updated'})

@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    db.session.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
    with db.session.begin():
        event = Event.query.get(event_id)
        if event:
            db.session.delete(event)
        else:
            return jsonify({'message': 'event not found'}), 404
    return jsonify({'message': 'event deleted'})

@app.route('/menus', methods=['GET'])
def get_menus():
    menus = Menu.query.all()
    return jsonify([{
        'menu_id': menu.menu_id,
        'menu_name': menu.menu_name,
        'description': menu.description,
        'price': menu.price
    } for menu in menus])

@app.route('/locations', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    return jsonify([{
        'location_id': location.location_id,
        'venue': location.venue,
        'address': location.address,
        'capacity': location.capacity
    } for location in locations])

@app.route('/report', methods=['GET'])
def generate_report():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    menu_id = request.args.get('menu_id')
    location_id = request.args.get('location_id')

    sql = """
    SELECT event_id, event_date, start, end, guest_count, menu_id, location_id
    FROM event
    WHERE 1=1
    """
    params = {}
    if start_date:
        sql += " AND event_date >= :start_date"
        params['start_date'] = start_date
    if end_date:
        sql += " AND event_date <= :end_date"
        params['end_date'] = end_date
    if menu_id:
        sql += " AND menu_id = :menu_id"
        params['menu_id'] = menu_id
    if location_id:
        sql += " AND location_id = :location_id"
        params['location_id'] = location_id

    result = db.session.execute(text(sql), params)
    events = result.mappings().all()

    total_events = len(events)
    average_duration = 0
    average_guests = 0
    if total_events > 0:
        total_duration = 0
        total_guests = 0
        for event in events:
            start_time = datetime.strptime(event['start'], '%H:%M')
            end_time = datetime.strptime(event['end'], '%H:%M')
            duration = (end_time - start_time).total_seconds() / 3600
            total_duration += duration
            total_guests += event['guest_count']
        average_duration = total_duration / total_events
        average_guests = total_guests / total_events

    events_list = [{
        'event_id': event['event_id'],
        'event_date': event['event_date'],
        'start': event['start'],
        'end': event['end'],
        'guest_count': event['guest_count'],
        'menu_id': event['menu_id'],
        'location_id': event['location_id']
    } for event in events]

    return jsonify({
        'total_events': total_events,
        'average_duration': average_duration,
        'average_guests': average_guests,
        'events': events_list
    })

@app.route('/')
@app.route('/<path:path>')
def serve_react_app(path=''):
    if path and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)