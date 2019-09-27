from flask import Flask, session
from flask_login import LoginManager

app = Flask(__name__)
static_folder = 'static'
app.config['SECRECT_KEP'] = 'Strong'
app.secret_key = 'any random string'

login_manager = LoginManager()
login_manager.init_app(app)


from Class import UserDataManager

@login_manager.user_loader
def load_user(username):
    userdata = UserDataManager()
    return userdata.get_user(username)



