from flask import *
from flask_login import UserMixin
from run import read_from_json_file, write_to_json_file,\
FILE
class UserDataManager(UserMixin):
    '''
    This class is used to manager user account information data.
    user data is store in json file with json formating

    _userdata : a dictionary of store all users' account information data

    for each user account has the data for:
        Username,
        password,
        Email
    '''

    def __init__(self):
        #obtain all user data from database
        self._userData = read_from_json_file(FILE)

    @property
    def data(self):
        return self._userData

    def get_user(self,username):
        if not self.is_existed(username):
            return None
        password = self._userData[username]['password']
        email = self._userData[username]['email']
        return User(username, password, email)

    #check if a existed user
    def is_existed(self, username):
        if username in self._userData.keys():
            return True
        return False

    #add new data into database
    def update_data(self, new_data):
        write_to_json_file(FILE, new_data)
        print(" data is updated!! ")

    #login check: check username and password
    def authentication(self, username, password):
        if self.is_existed(username) and self._userData[username]['password'] == password:
            return True
        return False

class User(UserMixin):
    '''
    User class contain account detail of per user

    username, password, email
    '''
    def __init__(self, username, password, email):
        self.id = username
        self.password = password
        self.email = email