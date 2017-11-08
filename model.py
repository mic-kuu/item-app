import random
import string

from itsdangerous import BadSignature, SignatureExpired, \
    TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

##
# MODEL DECLARATION (SQL ALCHEMY SETUP)
##

SECRET_KEY = ''.join(random.choice(string.ascii_uppercase + string.digits)
                     for x in range(32))

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    email = Column(String(128), unique=True)
    picture = Column(String(1024))

    def generate_auth_token(self, expiration=600):
        s = Serializer(SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)

        try:
            data = s.loads(token)
        except SignatureExpired:
            # Expired token
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id


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
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'picture': self.picture
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
            'id': self.id,
            'name': self.name,
            'price': self.description,
            'picture': self.picture,
            'description': self.picture,
            'user_id': self.user_id,
            'category_id': self.category_id
        }


engine = create_engine('sqlite:///itemsapp.db')

Base.metadata.create_all(engine)
