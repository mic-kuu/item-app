import json
import os
import random
import string
import uuid

import httplib2
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import make_response
from flask import session as login_session
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename

from database_setup import Base, Item, Category, User

# APP-WIDE PARAMETERS
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ico'}
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item App Application"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
engine = create_engine('sqlite:///itemsapp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def allowed_file(filename):
    """
    A helper function determining if user selected allowed picture extension
    :param filename: filename (name.extension)
    :return: True if extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def delete_picture(filename):
    """
    Finds appropriate picture in the uploads folder and deletes it
    :param filename: Name of the file with the extension
    """
    if filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        except OSError:
            print("There was an error deleting file: '{}'.".format(filename))


def api_error(message):
    """
    A helper function returning API error message
    :param message: Error message
    :return: JSON string
    """
    return jsonify({"error": message})


def api_success(message):
    """
    A helper function returning API success message
    :param message: Success message
    :return: JSON string
    """
    return jsonify({"success": message})


def process_user():
    """
    Process user that was authorized with Google. If user exists in DB
    returns it's id. If there is no user - creates a new one.

    :return: ID of the user
    """
    user = session.query(User).filter_by(email=login_session['email']).one_or_none()

    if user is None:
        user = User(username=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])

        session.add(user)
        session.commit()

    return user.id


@app.context_processor
def inject_user():
    """
    Adds context to the Jinija template. Returned variables are accessible
    in Jinija templates.
    :return: Variables from the returned dict will be accessible template.
    """

    user_name = "None"
    user_pic = "?"
    user_id = 0

    if 'username' in login_session:
        user_name = login_session['username']

    if 'picture' in login_session:
        user_pic = login_session['picture']

    if 'user_id' in login_session:
        user_id = login_session['user_id']

    return dict(user_name=user_name, user_pic=user_pic, user_id=user_id)


@app.errorhandler(404)
def page_not_found(e):
    # Custom 404 page template
    return render_template('404.html'), 404


@app.route('/login/')
def login_view():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', state=state)


@app.route('/gconnect', methods=['POST'])
def google_connect():
    """
    Authorizes app with Google Sign-In
    :return: Google Response
    """

    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()

    print(str(h.request(url, 'GET')[1]))

    result = json.loads(h.request(url, 'GET')[1].decode())
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # email has to be unique - so create a new user if email is not in DB
    user_id = process_user()
    login_session['user_id'] = user_id

    response = make_response(json.dumps('Successfuly logged in.'), 200)
    response.headers['Content-Type'] = 'application/json'

    return response


@app.route('/logout')
def google_logout():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']

    http = httplib2.Http()
    result = http.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Type'] = 'application/json'


    return redirect(url_for('login_view'))


@app.route('/')
def category_view():
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

    categories = session.query(Category).all()
    return render_template('view_category.html', categories=categories)


@app.route('/category/add', methods=['GET', 'POST'])
def category_add():
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

    if request.method == 'POST':

        new_category = Category(name=request.form['name'],
                                description=request.form['description'],
                                user_id=login_session['user_id'])

        picture = request.files['category-pic']

        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            extension = os.path.splitext(filename)[1]
            unique_filename = str(uuid.uuid4()) + str(extension)
            picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            new_category.picture = unique_filename

        session.add(new_category)
        session.commit()

        return redirect(url_for('category_view'))

    else:
        categories = session.query(Category).all()
        return render_template('add_category.html', categories=categories)


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def category_edit(category_id):
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

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

            delete_picture(edited_category.picture)

            edited_category.picture = unique_filename

        session.add(edited_category)
        session.commit()

        return redirect(url_for('category_view'))

    else:
        category = session.query(Category).filter_by(id=category_id).one()
        return render_template('edit_category.html', category=category)


@app.route('/category/<int:category_id>/')
def item_view(category_id):
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()

    return render_template('view_item.html', category=category, items=items)


@app.route('/item/add/', methods=['GET', 'POST'])
@app.route('/category/<int:category_id>/item/add', methods=['GET', 'POST'])
def item_add(category_id=1):
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

    if request.method == 'POST':

        new_item = Item(name=request.form['name'],
                        price=request.form['price'],
                        description=request.form['description'],
                        category_id=request.form['category-id'],
                        user_id=login_session['user_id'])

        picture = request.files['profile-pic']

        if picture and allowed_file(picture.filename):
            filename = secure_filename(picture.filename)
            extension = os.path.splitext(filename)[1]
            unique_filename = str(uuid.uuid4()) + str(extension)
            picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            new_item.picture = unique_filename

        session.add(new_item)
        session.commit()

        return redirect(url_for('item_view', category_id=request.form['category-id']))

    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories, category_id=category_id)


@app.route('/category/<int:category_id>/item/<int:item_id>/edit/', methods=['GET', 'POST'])
def item_edit(category_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

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

            delete_picture(edited_item.picture)
            edited_item.picture = unique_filename

        session.add(edited_item)
        session.commit()

        return redirect(url_for('item_view', category_id=request.form['category-id']))

    else:
        categories = session.query(Category).all()
        edited_item = session.query(Item).filter_by(category_id=category_id, id=item_id).one()
        return render_template('edit_item.html', categories=categories, category_id=category_id, item=edited_item)


@app.route('/category/<int:category>/item/<int:item>/delete/')
def item_delete(category, item):
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

    item = session.query(Item).filter_by(id=item, category_id=category).one_or_none()

    if item:
        delete_picture(item.picture)
        session.delete(item)
        session.commit()

    return redirect(url_for('item_view', category_id=category))


@app.route('/category/<int:category_id>/delete/')
def category_delete(category_id):
    if 'username' not in login_session:
        return redirect(url_for("login_view"))

    try:
        category = session.query(Category).filter_by(id=category_id).one()

    except NoResultFound:
        return api_error("There is no category with id: {}.".format(category_id))

    items = session.query(Item).filter_by(category_id=category.id).all()

    # delete all pictures - for items in category and for category
    for item in items:
        delete_picture(item.picture)
        session.delete(item)

    delete_picture(category.picture)

    session.delete(category)
    session.commit()

    return redirect(url_for('category_view'))


@app.route("/api/v1/categories/")
def categories_api():
    """
    Gets list of all categories - similar to category_view
    :return: JSON list of all categories
    """
    categories = session.query(Category).all()

    json_data = []
    for category in categories:
        json_data.append(category.serialize)

    return jsonify(categories=json_data)


@app.route("/api/v1/category/<int:category_id>", methods=['GET', 'PUT', 'DELETE'])
def category_api(category_id):
    """
    Deals with all category (single category) endpoints.
    GET - gets JSON description of category
    PUT - modifies chosen category
    DELETE - deletes chosen category
    :param category_id: id of the category, fetched from URL request
    :return: JSON message
    """
    try:
        category = session.query(Category).filter_by(id=category_id).one()

    except NoResultFound:
        return api_error("There is no category with id: %s. " % category_id)

    if request.method == 'GET':
        items = session.query(Item).filter_by(category_id=category_id).all()

        # building a response json with the category and all it's items
        items_list = []
        for item in items:
            items_list.append(item.serialize)

        json_data = {
            "category": category.serialize,
            "items": items_list
        }

        return jsonify(json_data)

    if request.method == 'PUT':
        request_json = request.get_json()

        if not request_json:
            return api_error("Nothing changed - empty JSON body.")

        if 'name' in request_json:
            category.name = request_json['name']
        if 'description' in request_json:
            category.description = request_json['description']

        session.add(category)
        session.commit()

        return api_success("Successfully modified category with id: %s." % category_id)

    if request.method == 'DELETE':
        items = session.query(Item).filter_by(category_id=category.id).all()

        for item in items:
            delete_picture(item.picture)
            session.delete(item)

        delete_picture(category.picture)

        session.delete(category)
        session.commit()

        return api_success("Successfully deleted category with id: %s and it's all items." % category_id)


@app.route("/api/v1/category/<int:category_id>/item/<int:item_id>", methods=['GET', 'PUT', 'DELETE'])
def item_api(category_id, item_id):
    """
    Deals with all item (single item) endpoints.
    GET - gets JSON description of item
    PUT - modifies chosen item
    DELETE - deletes chosen item
    :param category_id: id of the category, fetched from URL request
    :param item_id: id of the item, fetched from URL request
    :return: JSON message
    """
    try:
        item = session.query(Item).filter_by(id=item_id, category_id=category_id).one()

    except NoResultFound:
        return api_error("There is no item with id: {} in category with id: {}".format(item_id, category_id))

    if request.method == 'GET':
        return jsonify(item=item.serialize)

    if request.method == 'DELETE':
        delete_picture(item.picture)

        session.delete(item)
        session.commit()
        return api_success("Successfully deleted item with id: {} from category id: {}.").format(item_id, category_id)

    if request.method == 'PUT':
        request_json = request.get_json()

        if not request_json:
            return api_error("Nothing changed - empty JSON body.")

        if 'name' in request_json:
            item.name = request_json['name']
        if 'description' in request_json:
            item.description = request_json['description']
        if 'price' in request_json:
            item.description = request_json['price']

        session.add(item)
        session.commit()

        return api_success("Successfully modified item with id: {} from category id: {}.".format(item_id, category_id))


if __name__ == "__main__":
    # Note - for a production env change secret_key to a unique string and debug to False !
    app.secret_key = "this_is_my_secret"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
