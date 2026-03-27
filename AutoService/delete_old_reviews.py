from app import app, db, Review

with app.app_context():
    # Получаем все отзывы
    all_reviews = Review.query.all()
    
    print("Текущие отзывы в базе:")
    for r in all_reviews:
        print(f"ID: {r.id}, Рейтинг: {r.rating}, Комментарий: {r.comment[:50]}")
    
    # Удаляем отзывы с ID 1, 2, 3 (старые)
    for review_id in [1, 2, 3]:
        review = Review.query.get(review_id)
        if review:
            db.session.delete(review)
            print(f"Удален отзыв ID: {review_id}")
    
    db.session.commit()
    
    # Проверяем остались ли
    remaining = Review.query.all()
    print(f"\nОсталось отзывов: {len(remaining)}")
    for r in remaining:
        print(f"ID: {r.id}, Рейтинг: {r.rating}, Комментарий: {r.comment[:50]}")