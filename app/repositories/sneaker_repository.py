# sneaker_manager/app/repositories/sneaker_repository.py
from sqlalchemy.orm import Session
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
            color=sneaker_data["color"]
        )
        db.add(sneaker)
        db.commit()
        db.refresh(sneaker)
        return sneaker

    @staticmethod
    def get_all(db: Session):
        return db.query(Sneaker).all()

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