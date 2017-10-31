from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from passlib.apps import custom_app_context as pwd_context

from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    email = Column(String(128), unique=True)
    password_hash = Column(String(64))
    picture = Column(String(1024))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    picture = Column(String(250))

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'description' : self.description,
            'picture' : self.picture
        }


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    price = Column(String(8))
    picture = Column(String(250))
    description = Column(String(250))

    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'price' : self.description,
            'picture' : self.picture,
            'description' : self.picture,
            'user_id' : self.user_id,
            'category_id' : self.category_id
        }


engine  = create_engine('sqlite:///itemsapp.db')

Base.metadata.create_all(engine)
