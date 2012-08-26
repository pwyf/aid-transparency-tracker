from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask

def create_app():
    app = Flask("myapp")
    app.config.from_pyfile('config.py')
    return app 

app = create_app() 
db = SQLAlchemy(app)
Base = db.Model
init_db = db.create_all
db_session = db.session
