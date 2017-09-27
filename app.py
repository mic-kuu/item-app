from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Item, Category, User

app = Flask(__name__)
engine  = create_engine('sqlite:///itemsapp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/category/<int:category_id>/')
def mainView(category_id=1):
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category_id=category_id).all()

    return render_template('main.html', categories=categories, items=items, category_id=category_id)

@app.route('/category/add/')
def addCategory():
    return render_template('add_category.html')

@app.route('/category/<int:category_id>/add/')
def addItem(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('add_item.html', category=category)

if __name__ == "__main__":
    app.secret_key = "this_is_my_secret"
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)