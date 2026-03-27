from app import app, db, Review, User

with app.app_context():
    # Проверяем есть ли уже отзывы
    if Review.query.count() == 0:
        user = User.query.filter_by(username='user').first()
        if not user:
            user = User.query.first()
        
        if user:
            new_reviews = [
                Review(
                    user_id=user.id,
                    rating=5,
                    comment='Отличный сервис! Быстро, качественно, вежливые мастера. Рекомендую!',
                    is_approved=True
                ),
                Review(
                    user_id=user.id,
                    rating=4,
                    comment='Хорошо сделали, но пришлось немного подождать. В целом доволен.',
                    is_approved=True
                ),
                Review(
                    user_id=user.id,
                    rating=5,
                    comment='Лучший автосервис в городе! Обслуживаюсь здесь уже 2 года.',
                    is_approved=True
                ),
            ]
            
            for review in new_reviews:
                db.session.add(review)
            
            db.session.commit()
            print(f"Добавлено {len(new_reviews)} отзывов")
        else:
            print("Пользователь не найден")
    else:
        print(f"Отзывы уже есть: {Review.query.count()} шт.")