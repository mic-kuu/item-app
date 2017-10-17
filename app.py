import os
import uuid

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename

from database_setup import Base, Item, Category, User

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ico'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
engine = create_engine('sqlite:///itemsapp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def categoryView():
    categories = session.query(Category).all()
    return render_template('view_category.html', categories=categories)


@app.route('/category/<int:category_id>/')
def itemView(category_id):
    category = session.query(Category).filter_by(id=category_id).one()

    items = session.query(Item).filter_by(category_id=category_id).all()

    return render_template('view_item.html', category=category, items=items)


@app.route('/category/add', methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        new_category = Category(name=request.form['name'],
                                description=request.form['description'])

        picture = request.files['category-pic']

        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            extension = os.path.splitext(filename)[1]
            unique_filename = str(uuid.uuid4()) + str(extension)
            picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            new_category.picture = unique_filename

        session.add(new_category)
        session.commit()

        return redirect(url_for('categoryView'))

    else:
        categories = session.query(Category).all()
        return render_template('add_category.html', categories=categories)


@app.route('/item/add/', methods=['GET', 'POST'])
@app.route('/category/<int:category_id>/item/add', methods=['GET', 'POST'])
def addItem(category_id=1):
    if request.method == 'POST':

        new_item = Item(name=request.form['name'],
                        price=request.form['price'],
                        description=request.form['description'],
                        category_id=request.form['category-id'])

        picture = request.files['profile-pic']

        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            extension = os.path.splitext(filename)[1]
            unique_filename = str(uuid.uuid4()) + str(extension)
            picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            new_item.picture = unique_filename

        session.add(new_item)
        session.commit()

        return redirect(url_for('itemView', category_id=request.form['category-id']))

    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories, category_id=category_id)


@app.route('/category/<int:category_id>/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if request.method == 'POST':

        edited_item = session.query(Item).filter_by(category_id=category_id, id=item_id).one()

        edited_item.name = request.form['name']
        edited_item.price = request.form['price']
        edited_item.description = request.form['description']
        edited_item.category_id = request.form['category-id']

        file = request.files['profile-pic']

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)
            extension = os.path.splitext(filename)[1]

            unique_filename = str(uuid.uuid4()) + str(extension)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

            # delete old file (if there is any)
            if edited_item.picture:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], edited_item.picture))
            # and save filename of the new one
            edited_item.picture = unique_filename

        session.add(edited_item)
        session.commit()

        return redirect(url_for('itemView', category_id=request.form['category-id']))

    else:
        categories = session.query(Category).all()
        edited_item = session.query(Item).filter_by(category_id=category_id, id=item_id).one()
        return render_template('edit_item.html', categories=categories, category_id=category_id, item=edited_item)


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    if request.method == 'POST':

        edited_category = session.query(Category).filter_by(id=category_id).one()

        edited_category.name = request.form['name']
        edited_category.description = request.form['description']

        picture = request.files['category-pic']

        if picture and allowed_file(picture.filename):

            filename = secure_filename(picture.filename)
            extension = os.path.splitext(filename)[1]

            unique_filename = str(uuid.uuid4()) + str(extension)
            picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

            # delete old file (if there is any)
            if edited_category.picture:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], edited_category.picture))
                # and save filename of the new one
            edited_category.picture = unique_filename

        session.add(edited_category)
        session.commit()

        return redirect(url_for('categoryView'))

    else:
        category = session.query(Category).filter_by(id=category_id).one()
        return render_template('edit_category.html', category=category)


@app.route('/category/<int:category>/item/<int:item>/delete/')
def deleteItem(category, item):
    # TODO: Add handling on non-existing item delete
    item = session.query(Item).filter_by(id=item, category_id=category).one()
    session.delete(item)
    session.commit()

    # TODO: Add deleting of item picture

    return redirect(url_for('itemView', category_id=category))


@app.route('/category/<int:category_id>/delete/')
def deleteCategory(category_id):
    # TODO: Add handling on non-existing item delete
    category = session.query(Category).filter_by(id=category_id).one()

    session.delete(category)
    session.commit()

    # TODO: Add deleting of item picture + all items in the category

    return redirect(url_for('categoryView'))


if __name__ == "__main__":
    app.secret_key = "this_is_my_secret"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
