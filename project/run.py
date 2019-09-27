from login import app
import requests as req
import json

mykey = 'AIzaSyDfcnfzhKYnQfsY8ggX7UpK_3Ajvb9d25M'
zomato = '331dd26df311c5af96cde7a0f448537c'
tih = 'BFqkp4V35i0fXflQav9OYnolQuEMLGAg'
REC_FILE = 'database/recommandation.json'
FILE = 'database/userData.json'
LOCATION_DATA = 'database/near_location.json'
DETAILS_DATA = 'database/details.json'
EVENTS_DATA = 'database/events.json'
RESULTS_DATA = 'database/search_result.json'
DETAILS_TIH_DATA = 'database/details_tih.json'

def write_to_json_file(fileName, data):
    with open(fileName, 'w') as fp:
        json.dump(data, fp, indent=4)

def read_from_json_file(fileName):
    with open(fileName, 'r') as fp:
        data = json.load(fp)
    return data

def main():
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.917329664,151.225332432&radius=50000&type=restaurant&key={0}'.format(mykey)
    res = req.get(url)
    respond = json.loads(res.content)
    data = {}
    data['UNSW'] = {
        'category':'resturant',
        'results': respond['results']
    }
    write_to_json_file(LOCATION_DATA, data)

    #respond = json.dumps(respond, indent=4)
    #print(respond['results'])
    #print(type(respond))
    #print(respond)

if __name__ == '__main__':
    app.run(debug = True, port = 8080)


    '''
    default user detail
    '''
    User = {}
    User['gary'] = {
        "name": 'gary',
        "password":'1234',
        "email":"1234@gmail",
        "bank":{},
        "timetable":{}
    }
    #write_to_json_file(FILE, User)
