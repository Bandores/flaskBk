from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask import session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import relationship
import secrets
from sqlalchemy import or_
from forms import RatingCommentForm
app = Flask(__name__)

# Настройки подключения к базе данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = secrets.token_hex(16)
# Инициализация базы данных
db = SQLAlchemy(app)

# Модель для хранения информации о пользователях
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    events = db.relationship('Event', backref='organizer', lazy=True, overlaps="organizer")
    user_rating_comments = db.relationship('RatingComment', backref='comment_user', lazy=True, overlaps="comment_user,user_rating_comments")

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    date_time = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    info = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(200), nullable=True)
    event_comments = db.relationship("RatingComment", backref="rated_event", overlaps="event_comments,rated_event")
    user = relationship("User", back_populates="events")

class RatingComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)

    user = db.relationship("User", backref="rating_comments", overlaps="comment_user,user_rating_comments")
    event = db.relationship("Event", backref="comments", overlaps="event_comments,rated_event")


admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(RatingComment, db.session))

# Главная страница
@app.route('/')
def index():
    search_query = request.args.get('search', '')  # Получаем запрос поиска из URL
    filter_date = request.args.get('date', '')  # Получаем запрос по дате из URL
    filter_type = request.args.get('type', '')  # Получаем запрос по типу мероприятия из URL
    
    # Фильтрация мероприятий по запросу поиска
    if search_query:
        events = Event.query.filter(Event.name.contains(search_query))
    else:
        events = Event.query
    
    # Фильтрация мероприятий по дате
    if filter_date:
        events = events.filter(func.strftime('%Y-%m-%d', Event.date_time) == filter_date)
    
    # Фильтрация мероприятий по типу
    if filter_type:
        events = events.filter(Event.type == filter_type)
    
    events = events.all()  # Получение всех отфильтрованных мероприятий
    
    # Группировка мероприятий по типу для отображения в шаблоне
    events_by_type = {}
    for event in events:
        if event.type not in events_by_type:
            events_by_type[event.type] = []
        events_by_type[event.type].append(event)
    
    # Группировка мероприятий по дате для отображения в шаблоне
    events_by_date = {}
    for event in events:
        date_str = event.date_time.strftime('%Y-%m-%d')
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)
    
    # Получение уникальных типов мероприятий для отображения в выпадающем списке
    event_types = set([event.type for event in Event.query.all()])
    
    return render_template('index.html', events_by_type=events_by_type, events_by_date=events_by_date, event_types=event_types)
# Удаление мероприятия
@app.route('/delete_event', methods=['POST'])
def delete_event():
    event_id = request.form['event_id']
    event = Event.query.get(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Проверка логина пользователя и его аутентификация
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id  # Сохранение идентификатора пользователя в сессии
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))

        flash('Неправильное имя пользователя или пароль.', 'danger')

    return render_template('login.html')
# Страница добавления мероприятия
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Получаем текущего пользователя
        user = User.query.get(session['user_id'])
        date_time_str = request.form['date_time']
        date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
        type = request.form['type']
        name = request.form['name']
        address = request.form['address']
        info = request.form['info']
        photo = request.form['photo']
        event = Event(date_time=date_time, type=type, name=name, address=address, info=info, photo=photo, organizer=user)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_event.html')
# Фильтрация событий по типу и по дате
@app.before_request
def check_logged_in():
    if 'user_id' not in session and request.endpoint not in ['login', 'signup']:
        flash('Пожалуйста, войдите в систему, чтобы получить доступ к этой странице.', 'danger')
        return redirect(url_for('login'))
@app.route('/event_details/<int:event_id>', methods=['GET', 'POST'])
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    rating_comments = RatingComment.query.filter_by(event_id=event.id).all()
    user = None

    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Для добавления комментария необходимо войти в систему.', 'danger')
            return redirect(url_for('login'))

        rating = int(request.form['rating'])
        comment_text = request.form['comment']
        user_id = session['user_id']

        new_comment = RatingComment(user_id=user_id, event_id=event.id, rating=rating, comment=comment_text)
        db.session.add(new_comment)
        db.session.commit()

        flash('Ваш комментарий успешно добавлен!', 'success')
        return redirect(url_for('event_details', event_id=event.id))

    return render_template('event_details.html', event=event, rating_comments=rating_comments, user=user)
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
