from flask import Flask

#application = Flask(__name__)
from app import app as application

if __name__ == "__main__":
    application.run()
'''@application.route("/")
def hello():
    return "Getting ready2!!!!!!"

if __name__ == "__main__":
    application.run()

####################################3
import sys

# add your project directory to the sys.path
project_home = u'/home/morfisem/FreindlyServer'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# import flask app but need to call it "application" for WSGI to work
from app import app as application  # noqa
'''