from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Создание приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sharlandia.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модели данных
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(50))
    
    # Связь с категорией
    category = db.relationship('Category', back_populates='products')

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    author = db.Column(db.String(100), default='Admin')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    published = db.Column(db.Boolean, default=True)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    is_popular = db.Column(db.Boolean, default=False)  # Добавлено недостающее поле
    
    # Обратная связь с продуктами
    products = db.relationship('Product', back_populates='category')

class ColorOption(db.Model):
    __tablename__ = 'color_option'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hex_code = db.Column(db.String(7), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

# Маршруты
@app.route('/')
def index():
    try:
        # Проверяем существование таблицы
        inspector = db.inspect(db.engine)
        if 'category' not in inspector.get_table_names():
            return "База данных не инициализирована. Перезапустите приложение.", 500
            
        columns = [column['name'] for column in inspector.get_columns('category')]
        if 'is_popular' not in columns:
            return "База данных требует обновления. Удалите файл sharlandia.db и перезапустите приложение.", 500
        
        popular_categories = Category.query.filter_by(is_popular=True).all()
        all_categories = Category.query.all()
        blog_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(4).all()
        news_items = News.query.filter_by(published=True).order_by(News.created_at.desc()).limit(4).all()
        color_options = ColorOption.query.all()
        
        return render_template('index.html', 
                             popular_categories=popular_categories,
                             product_categories=all_categories,
                             blog_posts=blog_posts,
                             news_items=news_items,
                             color_options=color_options)
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"Ошибка загрузки страницы: {str(e)}", 500

@app.route('/catalog')
def catalog():
    try:
        categories = Category.query.all()
        products = Product.query.all()
        colors = ColorOption.query.all()
        return render_template('catalog.html', categories=categories, products=products, colors=colors)
    except Exception as e:
        print(f"Error in catalog route: {e}")
        return f"Ошибка загрузки каталога: {str(e)}", 500

@app.route('/blog')
def blog():
    try:
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
        return render_template('blog.html', posts=posts)
    except Exception as e:
        print(f"Error in blog route: {e}")
        return f"Ошибка загрузки блога: {str(e)}", 500

@app.route('/news')
def news():
    try:
        news_items = News.query.filter_by(published=True).order_by(News.created_at.desc()).all()
        return render_template('news.html', news_items=news_items)
    except Exception as e:
        print(f"Error in news route: {e}")
        return f"Ошибка загрузки новостей: {str(e)}", 500

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/search')
def search():
    try:
        query = request.args.get('q', '')
        products = Product.query.filter(Product.title.contains(query)).all()
        return render_template('search.html', products=products, query=query)
    except Exception as e:
        print(f"Error in search route: {e}")
        return f"Ошибка поиска: {str(e)}", 500

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        related_products = Product.query.filter(Product.category_id == product.category_id, Product.id != product_id).limit(4).all()
        return render_template('product_detail.html', product=product, related_products=related_products)
    except Exception as e:
        print(f"Error in product_detail route: {e}")
        return f"Ошибка загрузки товара: {str(e)}", 500

# Обработчик ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Запуск приложения
if __name__ == '__main__':
    with app.app_context():
        try:
            # Создаем все таблицы
            db.create_all()
            print("База данных успешно создана")
            
            # Проверяем, есть ли данные в таблице категорий
            inspector = db.inspect(db.engine)
            if 'category' in inspector.get_table_names():
                columns = [column['name'] for column in inspector.get_columns('category')]
                if 'is_popular' in columns and Category.query.count() == 0:
                    # Определяем данные здесь, чтобы они были доступны
                    categories_data = [
                        {'name': 'ШАРЫ ДЛЯ ДЕВОЧЕК', 'description': 'Наборы шаров для девочек', 'image_url': '/static/images/categories/girls.jpg', 'is_popular': True},
                        {'name': 'ШАРЫ ДЛЯ МАЛЬЧИКОВ', 'description': 'Наборы шаров для мальчиков', 'image_url': '/static/images/categories/boys.jpg', 'is_popular': True},
                        {'name': 'С ЦИФРАМИ', 'description': 'Наборы шаров с цифрами', 'image_url': '/static/images/categories/numbers.jpg', 'is_popular': True},
                        {'name': 'С БОЛЬШИМ ШАРОМ', 'description': 'Наборы шаров с большим шаром', 'image_url': '/static/images/categories/big_balloon.jpg', 'is_popular': True},
                        {'name': 'ШАРЫ ДЛЯ МУЖЧИН', 'description': 'Наборы шаров для мужчин', 'image_url': '/static/images/categories/men.jpg', 'is_popular': True},
                        {'name': 'ШАРЫ ДЛЯ ДЕВУШЕК', 'description': 'Наборы шаров для девушек', 'image_url': '/static/images/categories/women.jpg', 'is_popular': True},
                        {'name': 'ДЕВИЧНИК', 'description': 'Наборы шаров для девичника', 'image_url': '/static/images/categories/girls_party.jpg', 'is_popular': False},
                        {'name': 'ГЕНДЕРПАТИ', 'description': 'Наборы шаров для гендерпати', 'image_url': '/static/images/categories/gender_party.jpg', 'is_popular': False},
                        {'name': 'ВЫПИСКА ИЗ РОДДОМА', 'description': 'Наборы шаров для выписки из роддома', 'image_url': '/static/images/categories/hospital.jpg', 'is_popular': False},
                        {'name': '1 ГОДИК', 'description': 'Наборы шаров на 1 годик', 'image_url': '/static/images/categories/1_year.jpg', 'is_popular': False},
                        {'name': 'ФИГУРЫ ИЗ ШАРОВ', 'description': 'Фигуры из воздушных шаров', 'image_url': '/static/images/categories/figures.jpg', 'is_popular': False},
                        {'name': 'ОФОРМЛЕНИЕ ПРАЗДНИКОВ', 'description': 'Оформление праздников воздушными шарами', 'image_url': '/static/images/categories/decor.jpg', 'is_popular': False},
                        {'name': 'ЛАТЕКСНЫЕ ШАРЫ', 'description': 'Гелиевые латексные шары', 'image_url': '/static/images/categories/latex.jpg', 'is_popular': False},
                        {'name': 'ФОЛЬГИРОВАННЫЕ ШАРЫ', 'description': 'Гелиевые фольгированные шары', 'image_url': '/static/images/categories/foil.jpg', 'is_popular': False},
                        {'name': 'КОМПЛИМЕНТЫ И ПРИКОЛЫ', 'description': 'Комплименты и приколы на шарах', 'image_url': '/static/images/categories/jokes.jpg', 'is_popular': False},
                        {'name': 'КОРОБКИ СЮРПРИЗ', 'description': 'Коробки сюрприз с шарами', 'image_url': '/static/images/categories/surprise.jpg', 'is_popular': False},
                        {'name': 'ФОНТАНЫ ИЗ ШАРОВ', 'description': 'Фонтаны из воздушных шаров', 'image_url': '/static/images/categories/fountains.jpg', 'is_popular': False},
                        {'name': 'СТОЙКИ ИЗ ШАРОВ', 'description': 'Стойки из воздушных шаров', 'image_url': '/static/images/categories/stands.jpg', 'is_popular': False},
                    ]
                    
                    color_options_data = [
                        {'name': 'Белый и бежевый', 'hex_code': '#ffffff', 'is_active': True},
                        {'name': 'Чёрный', 'hex_code': '#000000', 'is_active': True},
                        {'name': 'Розовый', 'hex_code': '#ff99cc', 'is_active': True},
                        {'name': 'Розовое золото и пудровый', 'hex_code': '#e6b8cf', 'is_active': True},
                        {'name': 'Ярко-розовый', 'hex_code': '#ff00ff', 'is_active': True},
                        {'name': 'Голубой', 'hex_code': '#0099ff', 'is_active': True},
                        {'name': 'Синий', 'hex_code': '#0000ff', 'is_active': True},
                        {'name': 'Бирюзовый Тиффани', 'hex_code': '#009999', 'is_active': True},
                        {'name': 'Серебро', 'hex_code': '#cccccc', 'is_active': True},
                        {'name': 'Золото', 'hex_code': '#ffd700', 'is_active': True},
                        {'name': 'Сиреневый Фиолетовый', 'hex_code': '#9370db', 'is_active': True},
                        {'name': 'Красный', 'hex_code': '#ff0000', 'is_active': True},
                    ]
                    
                    for cat_data in categories_data:
                        category = Category(**cat_data)
                        db.session.add(category)
                    
                    for color_data in color_options_data:
                        color = ColorOption(**color_data)
                        db.session.add(color)
                    
                    db.session.commit()
                    print("Начальные данные успешно добавлены")
                else:
                    print("Данные уже существуют в базе данных или таблица не готова")
            else:
                print("Таблица category еще не создана")
                
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")
            # Удаляем файл базы данных и создаем заново
            try:
                import os
                if os.path.exists('sharlandia.db'):
                    os.remove('sharlandia.db')
                    print("Файл базы данных удален")
                
                # Пересоздаем базу данных
                db.create_all()
                print("База данных пересоздана")
                
                # Определяем данные здесь
                categories_data = [
                    {'name': 'ШАРЫ ДЛЯ ДЕВОЧЕК', 'description': 'Наборы шаров для девочек', 'image_url': '/static/images/categories/girls.jpg', 'is_popular': True},
                    {'name': 'ШАРЫ ДЛЯ МАЛЬЧИКОВ', 'description': 'Наборы шаров для мальчиков', 'image_url': '/static/images/categories/boys.jpg', 'is_popular': True},
                    {'name': 'С ЦИФРАМИ', 'description': 'Наборы шаров с цифрами', 'image_url': '/static/images/categories/numbers.jpg', 'is_popular': True},
                    {'name': 'С БОЛЬШИМ ШАРОМ', 'description': 'Наборы шаров с большим шаром', 'image_url': '/static/images/categories/big_balloon.jpg', 'is_popular': True},
                    {'name': 'ШАРЫ ДЛЯ МУЖЧИН', 'description': 'Наборы шаров для мужчин', 'image_url': '/static/images/categories/men.jpg', 'is_popular': True},
                    {'name': 'ШАРЫ ДЛЯ ДЕВУШЕК', 'description': 'Наборы шаров для девушек', 'image_url': '/static/images/categories/women.jpg', 'is_popular': True},
                    {'name': 'ДЕВИЧНИК', 'description': 'Наборы шаров для девичника', 'image_url': '/static/images/categories/girls_party.jpg', 'is_popular': False},
                    {'name': 'ГЕНДЕРПАТИ', 'description': 'Наборы шаров для гендерпати', 'image_url': '/static/images/categories/gender_party.jpg', 'is_popular': False},
                    {'name': 'ВЫПИСКА ИЗ РОДДОМА', 'description': 'Наборы шаров для выписки из роддома', 'image_url': '/static/images/categories/hospital.jpg', 'is_popular': False},
                    {'name': '1 ГОДИК', 'description': 'Наборы шаров на 1 годик', 'image_url': '/static/images/categories/1_year.jpg', 'is_popular': False},
                    {'name': 'ФИГУРЫ ИЗ ШАРОВ', 'description': 'Фигуры из воздушных шаров', 'image_url': '/static/images/categories/figures.jpg', 'is_popular': False},
                    {'name': 'ОФОРМЛЕНИЕ ПРАЗДНИКОВ', 'description': 'Оформление праздников воздушными шарами', 'image_url': '/static/images/categories/decor.jpg', 'is_popular': False},
                    {'name': 'ЛАТЕКСНЫЕ ШАРЫ', 'description': 'Гелиевые латексные шары', 'image_url': '/static/images/categories/latex.jpg', 'is_popular': False},
                    {'name': 'ФОЛЬГИРОВАННЫЕ ШАРЫ', 'description': 'Гелиевые фольгированные шары', 'image_url': '/static/images/categories/foil.jpg', 'is_popular': False},
                    {'name': 'КОМПЛИМЕНТЫ И ПРИКОЛЫ', 'description': 'Комплименты и приколы на шарах', 'image_url': '/static/images/categories/jokes.jpg', 'is_popular': False},
                    {'name': 'КОРОБКИ СЮРПРИЗ', 'description': 'Коробки сюрприз с шарами', 'image_url': '/static/images/categories/surprise.jpg', 'is_popular': False},
                    {'name': 'ФОНТАНЫ ИЗ ШАРОВ', 'description': 'Фонтаны из воздушных шаров', 'image_url': '/static/images/categories/fountains.jpg', 'is_popular': False},
                    {'name': 'СТОЙКИ ИЗ ШАРОВ', 'description': 'Стойки из воздушных шаров', 'image_url': '/static/images/categories/stands.jpg', 'is_popular': False},
                ]
                
                color_options_data = [
                    {'name': 'Белый и бежевый', 'hex_code': '#ffffff', 'is_active': True},
                    {'name': 'Чёрный', 'hex_code': '#000000', 'is_active': True},
                    {'name': 'Розовый', 'hex_code': '#ff99cc', 'is_active': True},
                    {'name': 'Розовое золото и пудровый', 'hex_code': '#e6b8cf', 'is_active': True},
                    {'name': 'Ярко-розовый', 'hex_code': '#ff00ff', 'is_active': True},
                    {'name': 'Голубой', 'hex_code': '#0099ff', 'is_active': True},
                    {'name': 'Синий', 'hex_code': '#0000ff', 'is_active': True},
                    {'name': 'Бирюзовый Тиффани', 'hex_code': '#009999', 'is_active': True},
                    {'name': 'Серебро', 'hex_code': '#cccccc', 'is_active': True},
                    {'name': 'Золото', 'hex_code': '#ffd700', 'is_active': True},
                    {'name': 'Сиреневый Фиолетовый', 'hex_code': '#9370db', 'is_active': True},
                    {'name': 'Красный', 'hex_code': '#ff0000', 'is_active': True},
                ]
                
                # Создаем таблицы заново
                db.create_all()
                
                # Добавляем данные
                for cat_data in categories_data:
                    category = Category(**cat_data)
                    db.session.add(category)
                
                for color_data in color_options_data:
                    color = ColorOption(**color_data)
                    db.session.add(color)
                
                db.session.commit()
                print("Начальные данные успешно добавлены после пересоздания БД")
            except Exception as e2:
                print(f"Ошибка при пересоздании базы данных: {e2}")
    
    app.run(debug=True)