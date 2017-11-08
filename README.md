# Project4: Item App 
This project is a result of Udcaity's Fullstack Developer Nanodegree assginment. The main goal was to prepare an Flask backend app for an Item Catalogue app with whole CRUD and external authentication.
![mic-kuu's item app catalogue view](https://i.imgur.com/XDixFlO.png)
## Overview
The application is written using python *Flask* framework in *python3.5.2*. It consists of web interface for browsing the catalogue of items 
and respective API endpoints. Data persistance is deliverd with *SQLite* database (*SQLAlchemy* on backend site). The frontend side of 
the app is rendered using *Jinija* templates. Styling was done with *Semantic* CSS framework. Basic interactivity of the site was achieved
with *jQurey*.

* The *app.py* is the starting point of the applicaton. It consits definition of all Views and Flask - related configurations.
* *client_secret*.json is not included in this repository, as it includes a private API key. It will be required to include your 
own for testing purposes
* *itemsapp.db* it's the SQLite database file. This repository has a simple app with filled data
* *model.py* it's definition of app's model (with SQLAlchemy)
* *static* folder has all static files
  * *main.css* has all custom styles for the app
  * all uploaded images are stored into the *static/uploads/* folder
* *templates* consits of all jinja templates used for rendering app

```
.
├── app.py
├── client_secret.json
├── itemsapp.db
├── model.py
├── static
│   ├── empty_img.png
│   ├── logo.png
│   ├── main.css
│   └── uploads
└── templates
    ├── 404.html
    ├── add_category.html
    ├── add_item.html
    ├── edit_category.html
    ├── edit_item.html
    ├── layout.html
    ├── login.html
    ├── view_category.html
    └── view_item.html
```
## How to use 
The [fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) has all required dependencies and configurations.
Simply clone this repository into the virtual machine with:

```
git clone
```

For security reasons the Google API keys were removed from this repository. In order to run this app, you'll need to provide your own credentials 
on [Google Developers Console](https://console.developers.google.com/apis).
The required steps are avaliable in the instructor notes - *Lesson 11: Creating Google Sign in - Step 5*. Following those steps you'll get a json file. 
Rename it to ```client_secret.json``` and place in the app's root directory. The json file will have similar structure to the one below:
```
{"web":{"client_id":"CLIENT_ID","project_id":"PROJECT_ID","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://accounts.google.com/o/oauth2/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"CLIENT_SECRET","redirect_uris":["http://localhost:5000/login/","http://localhost:5000/gconnect/"],"javascript_origins":["http://localhost:5000","https://localhost:5000"]}}
```

The database file for this project is preconfigured, but if there is a need to create an empty database, simply delete the *itemsapp.db* file and generate a new one with:

```
python3 model.py
```

Finally, you can run your server using the command below:

```
python3 app.py
```

## Contributions
Special thanks to:
* [Semantic UI](https://semantic-ui.com/) - for an awesome CSS framework
* [Flask](http://flask.pocoo.org/) - for the great, lightweight backend framework
* [Freepik](http://www.freepik.com/) - for the svg icons
* [Hero Patterns](http://www.heropatterns.com/) - for the great SVG bacground pattern
* [Unsplash](https://unsplash.com/) - for the most amazing, free images in the web 

## License
![Creative Commons License](https://i.creativecommons.org/l/by/4.0/88x31.png)  
This work is licensed under a [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/)
