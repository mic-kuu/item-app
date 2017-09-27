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

@app.route('/add/category/')
def addCategory():
    return render_template('add_category.html')

@app.route('/add/item/', methods=['GET', 'POST'])
def addItem():
    if request.method == 'POST':

        new_item = Item(name=request.form['name'],
                        price=request.form['price'],
                        description=request.form['description'],
                        category_id=request.form['category-id'])

        session.add(new_item)
        session.commit()

        return redirect(url_for('mainView', category_id=request.form['category-id']))

    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories)




if __name__ == "__main__":
    app.secret_key = "this_is_my_secret"
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)