from flask import *
from server import app
import json
from run import write_to_json_file, read_from_json_file, REC_FILE, LOCATION_DATA, DETAILS_DATA,\
EVENTS_DATA,tih,mykey,zomato, RESULTS_DATA, DETAILS_TIH_DATA
from Class import UserDataManager
from flask_login import login_user, login_required, current_user, logout_user
import requests as req
from implentation import get_rec, get_search_results, get_detail,get_events, get_search_results_by_tih,\
get_detail_tih,get_google_place_id, valid_table
from datetime import datetime, timedelta
import ast
import re
import copy



REC_FILE = 'recommandation.json'
@app.route('/')
def display_index():
    return redirect(url_for('home'))


@app.route('/login')
def display_login():
    return render_template("login.html")

@app.route('/check_login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        username = request.form['un']
        password = request.form['pass']

        #FIXME
        #put global variable for if logged in

        #getting user detail from database
        dataManager = UserDataManager()
        #converting json into dictionary
        #data = json.loads(data)
        #check username and password
        if dataManager.authentication(username, password):
            user = dataManager.get_user(username)
            login_user(user, remember=True)
            return redirect(url_for('home'))
        else:
            #show a error message that username or password is wron
            flash("Wrong usernmae or password!!!")
            return render_template("login.html")

    return render_template("login.html")

@app.route('/home')
def home():
    '''
    three recommandation place of sydney
    '''
    #FIXME how do we want to show recommandation
    places = ['Marina Bay Sands', 'Singapore Flyer','Night safari']
    #return value
    results = {};match_photos=[]
    get_rec(places, results, match_photos)

    #get events
    evt_keyword = 'singapore'
    events = []
    events = get_events(evt_keyword,'home_page')

    #get most visited
    most_visited = {}
    details = {}
    most_visited = read_from_json_file("database/most_visited.json")
    details = read_from_json_file("database/details_tih.json")
    topVisited = 0
    secondVisited = 0
    thirdVisited = 0
    mvPlaces = [None,None,None]
    for visitedPlaces in most_visited:
        visits = most_visited[visitedPlaces]["count"]
        if visits > topVisited:
            topVisited = visits
            mvPlaces[0] = visitedPlaces
        elif visits > secondVisited:
            secondVisited = visits
            mvPlaces[1] = visitedPlaces
        elif visits > thirdVisited:
            thirdVisited = visits
            mvPlaces[2] = visitedPlaces
    i = 0
    mvDetails = []
    while i < 3:
        mvDetails.append(get_detail_tih(mvPlaces[i]))
        mvDetails[i]["body"] = mvDetails[i]["body"][0:400] + "..."
        i += 1



    return render_template("home.html", results = results, photos=match_photos, events = events, mvDetails=mvDetails)

@app.route('/search_result')
def search_result():
    return render_template("search_result.html")

@app.route('/home/search_bar', methods=['POST','GET'])
def search_bar():
    if request.method == 'POST':
        cate = request.form.get('submit')
        keyword = request.form['search_input']
        print(request.form)
        #get resultes data
        #results = get_search_results(cate, keyword) #get search results by google map nearby api
        results = get_search_results_by_tih(cate, keyword) # get search results by tih api

        return render_template('search_result.html', results = results, category = cate.capitalize(), keyword=keyword.capitalize())
    return redirect(url_for("home"))

@app.route('/register')
def display_register():
    return render_template("register.html")

@app.route('/check_register', methods = ['POST','GET'])
def register():
    if(request.method == 'POST'):
        username = request.form['un']
        password = request.form['pass']
        confirm_pass = request.form['pass-check']
        email = request.form['email']

        #check if input a valid username and password
        if(username != "" and password != ""):
            '''
            storing data to our database
            '''
            dataManager = UserDataManager()
            #if it is not signed up, we add data
            if dataManager.is_existed(username) == False:
                #if the confirm passwords are wrong
                if password != confirm_pass:
                    flash("Passwords are not the same !!")
                    return redirect(url_for("display_register"))

                data = dataManager.data
                data[username] = {
                    "name": username,
                    "password":password,
                    "email":email,
                    "bank":{},
                    "timetable":{}
                }
                dataManager.update_data(data)
            else:
                flash("User already signed up !!")
                print("User already existed!")
                return redirect(url_for("display_register"))
        else:
            flash("Not a valid username/password !!")
            print("Pleas enter a valid username and password")
            return redirect(url_for("display_register"))

        flash("Sign up successfully !!")
        return redirect(url_for("display_login"))
    return render_template("register.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html"),404

@app.errorhandler(401)
def page_not_found(e):
    return render_template("error_require_login.html"),401

@app.route('/logout')
@login_required
def log_out():
    logout_user()
    flash("Logged out successfully !!")
    return redirect(url_for('display_login'))

'''
for detail, we would get following data from tih api to show up:
type, singaporeTourismAwards(if exist), email, description,tags
-need to fix map
'''
@app.route('/detail/<place_name>', methods=['GET','POST'])
def show_detail_by_name(place_name):
    if request.method == "POST":
        place = request.form.get('place_name')
        cate_by_search = request.form.get('category')
        keyword = request.form.get('keyword')
        '''
        1. get tih content by place name in !attraction!
        2. get place_id by the place name for google map
        3. get_detail()
        '''

        tih_url = 'https://tih-api.stb.gov.sg/content/v1/attractions/name/{0}?apikey={1}'.format(place, tih)
        tih_res = req.get(tih_url)
        tih_res = json.loads(tih_res.content)
        results = tih_res['data']

        url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={0}&Australia&inputtype=textquery&fields=place_id&key={1}'.format(place, mykey)
        res = req.get(url)
        res = json.loads(res.content)
        place_id = res['candidates'][0]['place_id']
        google_results = {}
        google_results = get_detail(place_id)
        results['google'] = google_results

        #get events
        category = results['categoryDescription']
        if(category == 'Accommodation'):
            category = 'Entertainment'
        events = []
        events = get_events(category)
        results['events'] = events

        #get suggested_places
        suggested_places = get_search_results_by_tih(cate_by_search.lower(), keyword, True, results['uuid'])

        return render_template('detailed.html', results = results, suggested_places = suggested_places)

@app.route('/detail/', methods=['GET','POST'])
def show_detail_by_id():
    if request.method == "POST":
        place_id = request.form.get('place_id')
        #cate and keyword is used for detail page suggested place. - enter datase to get more same category places
        cate_by_search = request.form.get('category')
        keyword = request.form.get('keyword')

        #results = get_detail(place_id)
        results = get_detail_tih(place_id)

        #get some more data from google map api
        google_id = get_google_place_id(results['name'])
        results_google = get_detail(google_id)
        results['google'] = results_google

        #get events
        category = results['categoryDescription']
        if(category == 'Accommodation'):
            category = 'Entertainment'
        events = []
        events = get_events(category)
        results['events'] = events

        #get suggested place
        suggested_places = get_search_results_by_tih(cate_by_search.lower(), keyword, True, place_id)
        #print(suggested_places)

        return render_template('detailed.html', results = results, suggested_places = suggested_places, category=cate_by_search, keyword=keyword)

@app.route('/event/<event_name>', methods=['GET','POST'])
def show_event(event_name):
    '''
    for event detail, we will the following in the web page
    - image, name+small description, start-end date, body(description), officialWebsite, tags, address, map(input as address)
    '''
    if request.method == 'POST':
        event = request.form.get('event_data')
        event = ast.literal_eval(event)
        #print(event)

        return render_template('event.html', event = event)

    return redirect(url_for('home'))

@app.route('/edit_profile')
@login_required
def display_edit():
    return render_template("edit_profile.html")

@app.route('/check_edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    if request.method == "POST":
        password = request.form['pass']
        confirm_pass = request.form['pass-check']
        email = request.form['email']
        username = current_user.id

        if(password != ""):
            '''
            storing data to our database
            '''
            dataManager = UserDataManager()

            #if the confirm passwords are wrong
            if password != confirm_pass:
                flash("Passwords are not the same !!")
                return redirect(url_for("display_edit"))

            data = dataManager.data
            data[username]["password"] = password;
            data[username]["email"] = email;
            print(data)
            dataManager.update_data(data)

            flash("Saved! Back to profile now")
            return redirect(url_for("display_edit"))
        else:
            flash("Not a valid new password !!")
            return redirect(url_for("display_edit"))

@app.route('/add/<place_name>', methods=['GET','POST'])
@login_required
def add_to_bank(place_name):
    '''
    For google matrix api to calculate distance.
    Basic usage: https://maps.googleapis.com/maps/api/distancematrix/json?parameters
    for parameters:
        - required parameters:
            - origins
                - need : place id or address
            - destinations
                - same as above
            # we need to store place id or address in our database when we press button "add to timetable"

            - apikey
        - optinal parameters(default model is driving )
            - language=en
            - mode
                - transit
                - driving
                - walking
            - if mode is transit, we can select transit mode
                - transit_mode = bus, train, tram, rail, subway
    '''
    if request.method == 'POST':
        #get place name and address
        place_name = request.form.get('add_bank');
        address = request.form.get('address');
        place_id = request.form.get('place_id')
        event = request.form.get('type');

        #store into our database
        username = current_user.id;
        dataManager = UserDataManager();
        data = dataManager.data;
        data[username]['bank'][place_name] = address;
        dataManager.update_data(data)

        #update most_visited && we dont want event in most vistied. bug
        if(event != 'event'):
            most_visited = [];
            most_visited = read_from_json_file("database/most_visited.json");
            if place_id in most_visited.keys():
                most_visited[place_id]["count"] += 1
            else:
                most_visited[place_id] = {
                    "count":1
                }
            write_to_json_file("database/most_visited.json",most_visited)


        userinfo = data[username];
        date = "2019-04-23"
    return render_template("profile.html", info = userinfo, key = 'none', default_date = date)

@app.route('/delete_bank', methods=['GET', 'POST'])
@login_required
def delete_bank():
    if request.method == 'POST':
        place_name = request.form.get('delete_place');

        #store into our database
        username = current_user.id;
        dataManager = UserDataManager();
        data = dataManager.data;
        #delete the place in database
        try:
            del data[username]['bank'][place_name];
        except:
            print("Not such a key")

        dataManager.update_data(data)

        userinfo = data[username];
        date = "2019-04-23"
    return render_template("profile.html", info = userinfo, key='none', default_date = date)


@app.route('/profile', methods=['GET','POST'])
@login_required
def display_profile():
    dataManager = UserDataManager()
    data = dataManager.data
    userinfo = data[current_user.id]
    date = "2019-04-23"
    return render_template("profile.html", info = userinfo, key = 'none', default_date = date)

@app.route('/generate', methods=['GET','POST'])
def generate():
    if request.method == "POST":
        form = request.form;
        #print(form)
        #if user did pick a week, dont play with database; otherwise display profile page again
        if 'start-day' in form.keys():
            timetable_date_key = form['start-day'];
            date = "2019-04-23";
            ts_type = form['transport-type'];

            #create temp key week data structure
            dt = datetime.strptime(timetable_date_key, '%Y-%m-%d')
            start = dt - timedelta(days=dt.weekday())
            end = start + timedelta(days=6)

            curr = start
            allDates = []
            while curr <= end:
                allDates.append(curr)
                curr = curr + timedelta(days=1)

            week_data = {
                "Mon": {'date':str(allDates[0])[0:10]},
                "Tue": {'date':str(allDates[1])[0:10]},
                "Wed": {'date':str(allDates[2])[0:10]},
                "Thu": {'date':str(allDates[3])[0:10]},
                "Fri": {'date':str(allDates[4])[0:10]},
                "Sat": {'date':str(allDates[5])[0:10]},
                "Sun": {'date':str(allDates[6])[0:10]}
            }

            #store all the events in our datebase
            for key,value in form.items():
                if key == 'start-day' or key == 'transport-type': continue;

                #get mon-sun day key, and time
                #get place name, address
                wk_day, time = key.split('-',2);
                place_name, address = value.split('==',2);
                week_data[wk_day][time]={
                    'name': place_name,
                    'address':address
                }

            #check if is a valid timetable
            dataManager = UserDataManager()
            data = dataManager.data
            if(valid_table(ts_type, week_data)):
                #everytime delete the data of the week first, then update. since we can double click in front-end to close some events
                #delete data of the week
                del data[current_user.id]['timetable'][timetable_date_key];

                data[current_user.id]['timetable'][timetable_date_key] = week_data;
                dataManager.update_data(data);
                flash("Valid timetable! Have a good time!!")
            else:
                pass
            return render_template('profile.html', info=data[current_user.id], key=timetable_date_key, default_date=date);

    return redirect(url_for('display_profile'))

@app.route('/get_date', methods=['POST'])
def get_date():
    start_date = request.form['start_date']

    dt = datetime.strptime(start_date, '%Y-%m-%d')
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)

    curr = start
    allDates = []
    while curr <= end:
        allDates.append(curr)
        curr = curr + timedelta(days=1)
    #print(allDates)
    key = str(allDates[0])[0:10] #start day
    date = str(dt)[0:10]

    dataManager = UserDataManager()
    data = dataManager.data
    userinfo = data[current_user.id]
    if key not in userinfo['timetable'].keys():
        userinfo['timetable'][key] = {
            "Mon": {'date':str(allDates[0])[0:10]},
            "Tue": {'date':str(allDates[1])[0:10]},
            "Wed": {'date':str(allDates[2])[0:10]},
            "Thu": {'date':str(allDates[3])[0:10]},
            "Fri": {'date':str(allDates[4])[0:10]},
            "Sat": {'date':str(allDates[5])[0:10]},
            "Sun": {'date':str(allDates[6])[0:10]}
        }
        dataManager.update_data(data)

    userinfo = UserDataManager().data[current_user.id]
    #print("This is the converted date: " + str(allDates[0])[0:10])
    #print(start)
    #print(end)
    #print(userinfo['timetable'][key]['Mon'])

    #later on, we want to show the timetable, if there are data store in that week FIXME
    return render_template("profile.html", info = userinfo, key = key, default_date = date)
