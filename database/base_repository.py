from sqlalchemy.orm import Session
from typing import Generic, TypeVar, Type, Optional, List, Union, Dict
from models.baseModel import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, data: Union[Dict, BaseModel]) -> T:
        if isinstance(data, BaseModel):
            db_item = data
        else:
            db_item = self.model(**data)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def get(self, db: Session, id: int) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, item: T) -> T:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def delete(self, db: Session, id: int) -> bool:
        db_item = self.get(db, id)
        if db_item:
            db.delete(db_item)
            db.commit()
            return True
        return False