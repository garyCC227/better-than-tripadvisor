from flask import *
import json
from login import write_to_json_file, read_from_json_file, REC_FILE, LOCATION_DATA, DETAILS_DATA,EVENTS_DATA,\
tih, mykey, zomato,RESULTS_DATA, DETAILS_TIH_DATA
import requests as req
import os

'''
need to consider if the url call status is not 200!!.  #FIXME later
'''
#function to get recommandation place detail
def get_rec(places, results, match_photos):
    data = read_from_json_file(REC_FILE)
    i = 0 #i for photos index
    for place in places:
        #firstly we search from own database, if we have the description of that place, we get data from our database
        if(place in data.keys()):
            results[place] = data[place]['description']
            match_photos.append(data[place]['photo_url'])
        #otherwise, we get a url call, base on the input keyword
        else:
            url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&exsentences=2&titles={}'.format(place)
            res = req.get(url)
            res = json.loads(res.content)
            details =  res['query']['pages'].values()
            #FIXME: search the photo by google map photo api call
            #FIXME: case sensitive
            #to avoid call google map api again, now just do it manually
            ph_1 = '/static/style/marina.jpg'
            ph_2 = '/static/style/singapore-flyer-03.jpg'
            ph_3 = '/static/style/night_safari.jpeg'
            match_photos = [ph_1, ph_2, ph_3]
            for detail in details:
                name = detail['title']
                description = detail['extract']
                results[name] = description

                #store the data into our json file
                data[name] = {
                    'description':description,
                    'photo_url':match_photos[i]
                }
            write_to_json_file(REC_FILE, data)
        i+=1


def get_events(keyword, page=None):
    '''
    none for others page, home for home page,
    home page will return 4 events, others page return 3 events
    '''
    if os.path.isfile(EVENTS_DATA) :
        data = read_from_json_file(EVENTS_DATA)
    else:
        data = {}

    #key is alway upper case
    if (keyword.upper() in data.keys()):
    #read from our database
        results = filter_events(data[keyword.upper()]['data'], page)
    else:
    #api call to get data
        url = 'https://tih-api.stb.gov.sg/content/v1/event/search?keyword={}&apikey={}'.format(keyword, tih)
        event_res = req.get(url)
        event_res = json.loads(event_res.content)

        #write to our database
        data[keyword.upper()] = event_res
        write_to_json_file(EVENTS_DATA, data)

        #filter 4 events as the return result
        results = filter_events(data[keyword.upper()]['data'], page)
    return results

def filter_events(events,page):
    if page == None:
        event_couter = 2
    else:
        event_couter = 1;
    filtered = []
    for event in events:
        filtered.append(event)
        if(event_couter==4):
            break
        event_couter+=1
    return filtered

#get search results by tih api
def get_search_results_by_tih(cate, keyword, is_suggested = False, place_id=None):
    if os.path.isfile(RESULTS_DATA) :
        data = read_from_json_file(RESULTS_DATA)
    else:
        data = {}

    '''
    1.for search resturant
        - first search food-beverages
        - 2nd search bars-clubs
    2.RESULTS_DATA file:
        #key is upper case
        key = keyword = {
            cate : cate, # if cate == resturant, cate value is food-beverages
            results : results
        }

    '''
    cate_more = ""
    if (cate == 'resturant'):
        cate = 'food-beverages'
        cate_more = 'bars-clubs'
    elif (cate == 'all'):
        cate = 'attractions'

    results = []
    if(keyword.upper() in data.keys() and cate.upper() == data[keyword.upper()]['category'].upper()):
        data = data[keyword.upper()]['results']
        results = filter_tih_results(data, is_suggested, place_id)
        return results
    else:
        url = 'https://tih-api.stb.gov.sg/content/v1/{2}/search?keyword={0}&apikey={1}'.format(keyword, tih, cate)
        result_res = req.get(url)
        results_res = json.loads(result_res.content)
        content = results_res['data']
        #print(len(content))
        #check if is resturant
        if cate_more == "bars-clubs":
            url = 'https://tih-api.stb.gov.sg/content/v1/{2}/search?keyword={0}&apikey={1}'.format(keyword, tih, cate_more)
            more_result_res = req.get(url)
            more_result_res = json.loads(more_result_res.content)
            more_content = more_result_res['data']
            content.extend(more_content)

        #print(len(content))
        #store in json file
        upper_key = keyword.upper()
        data[upper_key] = {
            'category':cate,
            'results': content
        }
        write_to_json_file(RESULTS_DATA ,data)

        #filter 10 results to front end
        new_data = data[upper_key]['results']
        results = filter_tih_results(new_data, is_suggested)
        #print(len(results))
        return results

def filter_tih_results(results, is_suggested=False, place_id=None):
    #print("hi")
    filtered = []
    i = 0;
    for result in results:
        #suggested place not overlap as the current place
        if place_id:
            if result['uuid'] == place_id:
                continue
        #we dont want the place without image as well
        if len(result['images']) == 0:
            continue
        address = result['address']['buildingName'] + ', ' + result['address']['block'] +' '+result['address']['streetName']
        result['address'] = address
        type = result['type'].replace("_", " ")
        #print(type)
        result['type'] = type
        filtered.append(result)

        if is_suggested:
            if i == 3:
                break;
        i+=1;

    #print(filtered)
    return filtered

#function to get search result by google map api
def get_search_results(cate, keyword):
    if os.path.isfile(LOCATION_DATA) :
        data = read_from_json_file(LOCATION_DATA)
    else:
        data = {}

    '''
    if we already searched this keyword and category, we get results from our
    database,
    otherwise we will do API call with the keyword and category, and also store
    data to our database.
    #store the keyword by upper letters

    #for url, we need to get geometry of the location by keyword. #FIXME
    '''
    results = []
    if(keyword.upper() in data.keys() and cate.upper() == data[keyword.upper()]['category'].upper()):
        data = data[keyword.upper()]['results']
        results = filter_data(data)
        return results
    else:
        #do the API call
        '''
        we have category, keyword.
        1. get geo location of the keyword,
        2. get nearbysearch API call
        3. store into our json database, by format:
            {keyword:{ # keyword must be uppercase
                type:category
                results:
                }
            }
        '''
        #1.
        geourl = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={0}&inputtype=textquery&fields=geometry&key={1}'.format(keyword, mykey)
        geores = req.get(geourl)
        geores = json.loads(geores.content)
        geolocation = geores['candidates'][0]['geometry']['location']
        longitude = geolocation['lng']
        latitude =  geolocation['lat']

        #2
        search_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={0},{1}&radius=1000&type=restaurant&key={2}'.format(latitude, longitude,mykey)
        search_res = req.get(search_url)
        search_res = json.loads(search_res.content)

        #3.
        upper_key = keyword.upper()
        data[upper_key] = {
            'category':cate,
            'results': search_res['results']
        }
        write_to_json_file(LOCATION_DATA, data)

        #return data
        new_data = data[upper_key]['results']
        results = filter_data(new_data)
        return results

''''
required data:(google map API)
placeid, name, opening_hours[open_now], photos[0][photo_reference],rating, types[0], vicinity
'''
def filter_data(data):
    results  = []
    #couter limits the number of resultes we want to show
    couter = 0
    for result in data:
        temp = {
            'place_id':result['place_id'],
            'name':result['name'],
            'type':result['types'][0],
            'address':result['vicinity']
        }
        if('opening_hours' in result.keys()):
            temp['open_now'] = result['opening_hours']['open_now']
        if( 'photos' in result.keys()):
            temp['photo_reference'] = result['photos'][0]['photo_reference']
        if( 'rating' in result.keys()):
            temp['rating'] = result['rating']
        #make a \n for every 3 char in name
        name = temp['name']
        word_couter = 1
        formatted_name = []
        for word in name.split(' '):
            if( word_couter % 3 == 0):
                word+=' <br>'
            word_couter+=1
            formatted_name.append(word)
        formatted_name = ' '.join(formatted_name)
        temp['name'] = formatted_name

        results.append(temp)
        couter+=1
        if (couter == 10): break;

    return results

#get detail by tih by uuid
def get_detail_tih(place_id):
    if os.path.isfile(DETAILS_TIH_DATA) :
        data = read_from_json_file(DETAILS_TIH_DATA)
    else:
        data = {}

    if place_id in data.keys():
        result = data[place_id]
    else:
        url = 'https://tih-api.stb.gov.sg/content/v1/search?dataset=accommodation&dataset=attractions&dataset=bars_clubs&dataset=event&dataset=food_beverages&dataset=shops&dataset=tour&dataset=venue&dataset=walking_trail'+\
        '&keyword={}&apikey={}'.format(place_id, tih)
        res = req.get(url)
        res = json.loads(res.content)
        result = res['data'][0]['results']
        data[place_id] = result
        write_to_json_file(DETAILS_TIH_DATA, data)

    #change format #[0], since the api is an array, and array[0] is the data
    type = result[0]['type'].replace("_", " ")
    result[0]['type'] = type

    return result[0]

def get_google_place_id(place):
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={0}&Australia&inputtype=textquery&fields=place_id&key={1}'.format(place, mykey)
    res = req.get(url)
    res = json.loads(res.content)
    place_id = res['candidates'][0]['place_id']
    return place_id

#get detail from google map API
def get_detail(place_id):

    if os.path.isfile(DETAILS_DATA) :
        data = read_from_json_file(DETAILS_DATA)
    else:
        data = {}

    '''
    check if we have the detail of the place in database
    '''
    if place_id in data.keys():
        results = data[place_id]['result']
        results = filter_photos(results)
        return results
    else:
        url = 'https://maps.googleapis.com/maps/api/place/details/json?placeid={0}&fields=formatted_address,formatted_phone_number,name,opening_hours,photos,rating,reviews,types,url,website&key={1}'.format(place_id, mykey)
        res = req.get(url)
        res = json.loads(res.content)
        data[place_id] = res
        write_to_json_file(DETAILS_DATA, data)
        results = res['result']
        results = filter_photos(results)
        return results

def filter_photos(results):
    filter_result = results
    photos = results['photos']
    filter_photo = []
    couter = 0
    for photo in photos:
        filter_photo.append(photo)
        couter+=1
        if(couter == 3): break;

    filter_result['photo'] = filter_photo
    #print(filter_photo)
    return filter_result

#FIXME  generate a valid timetable or not
def valid_table(ts_type, week_data):
    valid = True;
    for day in week_data.keys():
        #if there only 2 key, mean there is only one event at that day, and another key is date
        if len(week_data[day].keys()) <= 2: continue;
        tp = list(week_data[day].keys());
        temp = [];
        for element in tp:
            if element == 'date': continue;
            temp.append(int(element));
        temp.sort()

        #check valid time gap for all the adjacent events in this day
        for i in range(len(temp) - 1):
            #i & i + 1
            address1 = week_data[day][str(temp[i])]['address'];
            address2 = week_data[day][str(temp[i+1])]['address'];
            table_time = temp[i+1] - temp[i] - 1; #9, 10, time gap is 0

            if('ingapore' not in address1): #we only do singapore #FIXME if we want to other cities
                address1 +=' singapore';
            elif('ingapore' not in address2):
                address2 +=' singapore';

            #get time from api call
            url = 'https://maps.googleapis.com/maps/api/distancematrix/json?key={0}&origins={1}&destinations={2}'.format(mykey, address1, address2);
            if ts_type == 'bus' or ts_type =='train':
                url+='&mode=transit&transit_mode={0}'.format(ts_type);
            else:
                url+='&mode={}'.format(ts_type);

            res = req.get(url);
            res = json.loads(res.content);
            if ('duration' not in res['rows'][0]['elements'][0].keys() ) :continue;
            google_time = res['rows'][0]['elements'][0]['duration']['text'];
            google_sec = res['rows'][0]['elements'][0]['duration']['value'];

            table_sec = table_time * 3600;

            #check if time is not valid, then we flash a reminder;
            #if the time gap in timetable is 0 hours, then we consider 10mins travel will be ok
            place1 = week_data[day][str(temp[i])]['name'];
            place2 = week_data[day][str(temp[i+1])]['name'];
            if table_time == 0:
                if google_sec > 600:
                    valid = False;
                    flash("<span class='text-dark'>< {0} > to < {1} > by '{3}' needs at least </span> {2}".format(place1, place2, google_time,ts_type));
            else:
                if table_sec < google_sec:
                    valid = False;
                    flash("<span class='text-dark'>< {0} > to < {1} > by '{3}' needs at least </span> {2}".format(place1, place2, google_time, ts_type));
            #print(google_sec)
            #print(table_sec)

    return valid;




if __name__ == '__main__':
    get_detail_tih('00540bbe0cb27a94698ab2bdbce59a0c91c')
