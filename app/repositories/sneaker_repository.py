# sneaker_manager/app/repositories/sneaker_repository.py
from sqlalchemy.orm import Session, joinedload
from ..models import Sneaker, Rating


class SneakerRepository:
    @staticmethod
    def create(db: Session, sneaker_data: dict):
        sneaker = Sneaker(
            #id = sneaker_data["id"],
            name=sneaker_data["name"],
            brand=sneaker_data["brand"],
            series=sneaker_data["series"],
            purchase_date=sneaker_data["purchase_date"],
            purchase_price=sneaker_data["purchase_price"],
            image_path=sneaker_data["image_path"],
            size=sneaker_data["size"],
            color=sneaker_data["color"],
            status=sneaker_data.get("status", "使用中")  # ← 新增这一行
        )
        db.add(sneaker)
        db.commit()
        db.refresh(sneaker)
        return sneaker

    @staticmethod
    def get_all(db: Session):
        return db.query(Sneaker).options(joinedload(Sneaker.ratings)).all()

    @staticmethod
    def delete(db: Session, sneaker_id: int):
        sneaker = db.query(Sneaker).filter(Sneaker.id == sneaker_id).first()
        if sneaker:
            db.delete(sneaker)
            db.commit()
            return True
        return False

    @staticmethod
    def add_rating(db: Session, sneaker_id, cushion, traction, torsion, durability):
        rating = Rating(
            sneaker_id=sneaker_id,
            cushion=cushion,
            traction=traction,
            torsion=torsion,
            durability=durability
        )
        db.add(rating)
        db.commit()
        return rating

    @staticmethod
    def update(db: Session, sneaker_id: int, sneaker_data: dict):
        sneaker = db.query(Sneaker).filter_by(id=sneaker_id).first()
        if not sneaker:
            raise ValueError("未找到该球鞋")
        for k, v in sneaker_data.items():
            setattr(sneaker, k, v)
        db.commit()
        db.refresh(sneaker)
        return sneaker

