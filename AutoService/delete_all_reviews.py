from app import app, db, Review

with app.app_context():
    # Удаляем все отзывы
    count = Review.query.count()
    Review.query.delete()
    db.session.commit()
    print(f"Удалено {count} отзывов")
    
    # Проверка
    remaining = Review.query.count()
    print(f"Осталось отзывов: {remaining}")