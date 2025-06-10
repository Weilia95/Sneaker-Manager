# app/repositories/rating_repository.py
from app.models import Rating


def get_all_ratings_by_sneaker_id(sneaker_id):
    """
    获取某双球鞋的所有评分记录
    """
    return Rating.query.filter_by(sneaker_id=sneaker_id).all()


def add_rating(session, sneaker_id, cushion, traction, torsion, durability):
    """
    添加一条新的评分记录
    """
    new_rating = Rating(
        sneaker_id=sneaker_id,
        cushion=cushion,
        traction=traction,
        torsion=torsion,
        durability=durability
    )
    session.add(new_rating)
    session.commit()
