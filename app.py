from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from datetime import datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)

# Настройки подключения к базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)


# Модель для хранения информации о пользователях
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Модель для хранения информации о мероприятиях
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    info = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(200), nullable=True)


# Главная страница
@app.route('/')
def index():
    events = Event.query.all()
    # Группировка мероприятий по типам
    events_by_type = {}
    for event in events:
        if event.type not in events_by_type:
            events_by_type[event.type] = []
        events_by_type[event.type].append(event)

    # Группировка мероприятий по датам
    events_by_date = {}
    for event in events:
        date_str = event.date_time.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)

    return render_template('index.html', events_by_type=events_by_type, events_by_date=events_by_date)


# Страница добавления мероприятия
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        date_time_str = request.form['date_time']
        date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        type = request.form['type']
        name = request.form['name']
        address = request.form['address']
        info = request.form['info']
        photo = request.form['photo']
        event = Event(date_time=date_time, type=type, name=name, address=address, info=info, photo=photo)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_event.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)