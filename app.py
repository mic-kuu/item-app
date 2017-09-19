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
def mainView():
    categories = session.query(Category).all()

    return render_template('main.html', categories=categories)

# A simple endpoint prepared for development purposes
@app.route('/add/<string:name>/')
def addCategory(name):
        new_category = Category(name = name)
        session.add(new_category)
        session.commit()
        return redirect(url_for("mainView"))

if __name__ == "__main__":
    app.secret_key = "this_is_my_secret"
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)