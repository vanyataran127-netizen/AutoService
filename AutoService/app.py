import os
import re 
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///autoservice.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer)
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    car_brand = db.Column(db.String(50))
    car_model = db.Column(db.String(50))
    car_year = db.Column(db.Integer)
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending')
    total_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='orders')
    service = db.relationship('Service', backref='orders')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='reviews')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

# Декораторы
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'admin':
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Маршруты
@app.route('/')
def index():
    services = Service.query.filter_by(is_active=True).limit(6).all()
    reviews = Review.query.filter_by(is_approved=True).limit(3).all()
    news = News.query.filter_by(is_published=True).limit(3).all()
    return render_template('index.html', services=services, reviews=reviews, news=news)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            flash(f'Добро пожаловать, {user.username}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('auth.html', action='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        
        if not username or not email or not password:
            flash('Пожалуйста, заполните все обязательные поля', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('Пароль должен содержать минимум 8 символов', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже существует', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'danger')
            return redirect(url_for('register'))
        
        if phone:
            pass
        
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти в систему.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth.html', action='register')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/services')
def services():
    service_id = request.args.get('id')
    if service_id:
        service = Service.query.get_or_404(service_id)
        return render_template('services.html', service=service, view='detail')
    
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Service.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Service.name.contains(search) | Service.description.contains(search))
    
    services = query.all()
    categories = db.session.query(Service.category).distinct().all()
    
    return render_template('services.html', services=services, categories=categories, view='list')

@app.route('/booking/<int:service_id>', methods=['GET', 'POST'])
@login_required
def booking(service_id):
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'POST':
        order = Order(
            user_id=session['user_id'],
            service_id=service.id,
            car_brand=request.form.get('car_brand'),
            car_model=request.form.get('car_model'),
            car_year=request.form.get('car_year'),
            appointment_date=datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%dT%H:%M'),
            total_price=service.price,
            notes=request.form.get('notes'),
            status='pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash(f'Заказ #{order.id} успешно создан!', 'success')
        return redirect(url_for('orders'))
    
    return render_template('booking.html', service=service)

@app.route('/orders')
@login_required
def orders():
    order_id = request.args.get('id')
    if order_id:
        order = Order.query.get_or_404(order_id)
        if order.user_id == session['user_id'] or session['role'] == 'admin':
            return render_template('orders.html', order=order, view='detail')
    
    status = request.args.get('status')
    query = Order.query.filter_by(user_id=session['user_id'])
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('orders.html', orders=orders, view='list')

@app.route('/cancel-order/<int:order_id>')
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != session['user_id'] and session['role'] != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('orders'))
    
    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        db.session.commit()
        flash('Заказ успешно отменен', 'success')
    else:
        flash('Невозможно отменить заказ в текущем статусе', 'warning')
    
    return redirect(url_for('orders'))

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if request.method == 'POST' and session.get('user_id'):
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')
        order_id = request.form.get('order_id')
        
        existing = Review.query.filter_by(order_id=order_id).first()
        if existing:
            flash('Вы уже оставляли отзыв на этот заказ', 'warning')
            return redirect(url_for('reviews'))
        
        review = Review(
            user_id=session['user_id'],
            order_id=order_id,
            rating=rating,
            comment=comment,
            is_approved=False
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Спасибо за отзыв! Он будет опубликован после модерации.', 'success')
        return redirect(url_for('reviews'))
    
    reviews_list = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
    return render_template('reviews.html', reviews=reviews_list)

@app.route('/news')
def news():
    news_id = request.args.get('id')
    if news_id:
        news_item = News.query.get_or_404(news_id)
        return render_template('news.html', news=news_item, view='detail')
    
    news_list = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    return render_template('news.html', news_list=news_list, view='list')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')
        
        if request.form.get('new_password'):
            if request.form.get('new_password') == request.form.get('confirm_password'):
                user.set_password(request.form.get('new_password'))
                flash('Пароль успешно изменен', 'success')
            else:
                flash('Пароли не совпадают', 'danger')
                return redirect(url_for('profile'))
        
        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

# Админ панель
@app.route('/admin')
@admin_required
def admin_dashboard():
    section = request.args.get('section', 'dashboard')
    entity_id = request.args.get('id')
    
    users = User.query.order_by(User.created_at.desc()).all() if section in ['users', 'edit_user'] else []
    services = Service.query.order_by(Service.created_at.desc()).all() if section in ['services', 'edit_service'] else []
    orders = Order.query.order_by(Order.created_at.desc()).all() if section in ['orders'] else []
    reviews = Review.query.order_by(Review.created_at.desc()).all() if section in ['reviews'] else []
    news = News.query.order_by(News.created_at.desc()).all() if section in ['news', 'edit_news'] else []
    
    edit_item = None
    if entity_id:
        if section == 'edit_user':
            edit_item = User.query.get(entity_id)
        elif section == 'edit_service':
            edit_item = Service.query.get(entity_id)
        elif section == 'edit_news':
            edit_item = News.query.get(entity_id)
    
    stats = {
        'total_users': User.query.count(),
        'total_orders': Order.query.count(),
        'total_services': Service.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'monthly_revenue': db.session.query(db.func.sum(Order.total_price)).filter(
            Order.status == 'completed',
            Order.created_at >= datetime.now().replace(day=1)
        ).scalar() or 0
    }
    
    return render_template('admin.html', 
                         section=section, 
                         users=users, 
                         services=services,
                         orders=orders,
                         reviews=reviews,
                         news=news,
                         edit_item=edit_item,
                         stats=stats)

@app.route('/admin/<action>/<entity>', methods=['POST'])
@admin_required
def admin_action(action, entity):
    if action == 'add':
        if entity == 'service':
            service = Service(
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(request.form.get('price')),
                duration=int(request.form.get('duration')),
                category=request.form.get('category'),
                is_active='is_active' in request.form
            )
            db.session.add(service)
            flash('Услуга добавлена', 'success')
        
        elif entity == 'news':
            news = News(
                title=request.form.get('title'),
                content=request.form.get('content'),
                is_published='is_published' in request.form
            )
            db.session.add(news)
            flash('Новость добавлена', 'success')
    
    elif action == 'edit':
        if entity == 'service':
            service = Service.query.get(request.form.get('id'))
            service.name = request.form.get('name')
            service.description = request.form.get('description')
            service.price = float(request.form.get('price'))
            service.duration = int(request.form.get('duration'))
            service.category = request.form.get('category')
            service.is_active = 'is_active' in request.form
            flash('Услуга обновлена', 'success')
        
        elif entity == 'user':
            user = User.query.get(request.form.get('id'))
            user.role = request.form.get('role')
            user.is_active = 'is_active' in request.form
            flash('Пользователь обновлен', 'success')
        
        elif entity == 'news':
            news = News.query.get(request.form.get('id'))
            news.title = request.form.get('title')
            news.content = request.form.get('content')
            news.is_published = 'is_published' in request.form
            flash('Новость обновлена', 'success')
    
    elif action == 'delete':
        if entity == 'service':
            service = Service.query.get(request.form.get('id'))
            db.session.delete(service)
            flash('Услуга удалена', 'success')
        elif entity == 'review':
            review = Review.query.get(request.form.get('id'))
            db.session.delete(review)
            flash('Отзыв удален', 'success')
    
    elif action == 'approve':
        if entity == 'review':
            review = Review.query.get(request.form.get('id'))
            review.is_approved = True
            flash('Отзыв опубликован', 'success')
    
    elif action == 'update_status':
        if entity == 'order':
            order = Order.query.get(request.form.get('id'))
            order.status = request.form.get('status')
            flash('Статус обновлен', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard', section=entity + 's'))

# Функция для создания тестовых данных
def init_db():
    with app.app_context():
        db.create_all()
        
        # Создание админа если нет
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@autoservice.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin / admin123")
        
        # Создание тестового пользователя если нет
        if not User.query.filter_by(username='user').first():
            user = User(
                username='user',
                email='user@mail.com',
                role='user',
                is_active=True,
                phone='+7 999 123-45-67',
                address='г. Москва, ул. Тестовая, д. 1'
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            print("Test user created: user / user123")
        
        # Создание тестовых услуг ТОЛЬКО если нет услуг
        if Service.query.count() == 0:
            test_services = [
                Service(name='Замена масла', description='Полная замена моторного масла с заменой масляного фильтра.', price=2500, duration=60, category='Техобслуживание', is_active=True),
                Service(name='Диагностика двигателя', description='Компьютерная диагностика двигателя, проверка всех систем.', price=1500, duration=45, category='Диагностика', is_active=True),
                Service(name='Замена тормозных колодок', description='Замена передних и задних тормозных колодок.', price=3000, duration=90, category='Ремонт', is_active=True),
                Service(name='Шиномонтаж', description='Сезонная смена шин, балансировка колес.', price=2000, duration=60, category='Шиномонтаж', is_active=True),
                Service(name='Ремонт подвески', description='Диагностика и ремонт ходовой части.', price=4000, duration=120, category='Ремонт', is_active=True),
                Service(name='Чистка инжектора', description='Ультразвуковая чистка форсунок.', price=3500, duration=90, category='Диагностика', is_active=True),
            ]
            for service in test_services:
                db.session.add(service)
            db.session.commit()
            print(f"Created {len(test_services)} services")
        
        # Создание тестовых заказов ТОЛЬКО если нет заказов
        if Order.query.count() == 0:
            user = User.query.filter_by(username='user').first()
            admin = User.query.filter_by(username='admin').first()
            services = Service.query.all()
            
            from datetime import timedelta
            
            if services:
                test_orders = []
                
                if len(services) > 0:
                    test_orders.append(Order(
                        user_id=user.id,
                        service_id=services[0].id,
                        car_brand='Toyota',
                        car_model='Camry',
                        car_year=2020,
                        appointment_date=datetime.now() + timedelta(days=2),
                        status='pending',
                        total_price=services[0].price,
                        notes='Прошу позвонить перед записью'
                    ))
                
                if len(services) > 1:
                    test_orders.append(Order(
                        user_id=user.id,
                        service_id=services[1].id,
                        car_brand='Hyundai',
                        car_model='Solaris',
                        car_year=2019,
                        appointment_date=datetime.now() + timedelta(days=3),
                        status='confirmed',
                        total_price=services[1].price,
                        notes='Чек нужен для отчета'
                    ))
                
                if len(services) > 2:
                    test_orders.append(Order(
                        user_id=user.id,
                        service_id=services[2].id,
                        car_brand='Kia',
                        car_model='Rio',
                        car_year=2018,
                        appointment_date=datetime.now() - timedelta(days=5),
                        status='completed',
                        total_price=services[2].price,
                        notes='Работой доволен'
                    ))
                
                for order in test_orders:
                    db.session.add(order)
                db.session.commit()
                print(f"Created {len(test_orders)} orders")
        
        if News.query.count() == 0:
            test_news = [
                News(title='Открытие нового автосервиса!', content='Мы рады сообщить об открытии нового современного автосервиса. Ждем вас!', is_published=True),
                News(title='Акция: Диагностика бесплатно!', content='При любом ремонте диагностика в подарок!', is_published=True),
                News(title='Новогодние скидки', content='Скидка 20% на все виды работ!', is_published=True),
            ]
            for news in test_news:
                db.session.add(news)
            db.session.commit()
            print(f"Created {len(test_news)} news")
        
        print("Database initialization completed!")

if __name__ == '__main__':
    # Инициализация базы данных
    with app.app_context():
        db.create_all()
        init_db()
    
    app.run(debug=True)