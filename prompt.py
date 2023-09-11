import googlemaps, urllib3, json,requests, time, shutil, os
from datetime import datetime
from termcolor import colored
import qwikidata
import qwikidata.sparql
import pics

http = urllib3.PoolManager()

with open("apiKey.txt", "r") as file:
    keys = json.load(file)
    imgGen_key, mapsApi_key, weatherApi_key = keys["imgGen_key"], keys["mapsApi_key"], keys["weatherApi_key"]
parent_dir = os.getcwd()+'/generatedImages/'
map_client = googlemaps.Client(mapsApi_key)
#(lat, lng) = (40.752250, -73.981064)
lat = float(input("lat. : "))
lng = float(input("lon. : "))
pics_format = [576,784][0]

def get_city_wikidata(city, country):
    query = """
    SELECT ?population
    WHERE
    {
      ?city rdfs:label '%s'@en.
      ?city wdt:P1082 ?population.
      ?city wdt:P17 ?country.
      ?city rdfs:label ?cityLabel.
      ?country rdfs:label ?countryLabel.
      FILTER(LANG(?cityLabel) = "en").
      FILTER(LANG(?countryLabel) = "en").
      FILTER(CONTAINS(?countryLabel, "%s")).
    }
    """ % (city, country)
    res = qwikidata.sparql.return_sparql_query_results(query)
    out = res['results']['bindings']
    if out:
        return True, int(out[0]['population']['value'])
    return False, None
def get_places(radius):
    points_of_interest = ['port','airport','amusement_park','aquarium','art_gallery','bakery','bar','book_store','bowling_alley','cafe','casino','cemetery','church','drugstore','embassy','fire_station','florist','gas_station','train_station','hindu_temple','laundry','library','mosque','movie_theater','museum','park','pharmacy','post_office','restaurant','school','secondary_school','stadium','store','subway_station','supermarket','synagogue','university','zoo','natural_feature','landmark']
    places_list = []
    responseA = map_client.places_nearby(
        location=(lat, lng),
        radius=radius
    )
    places_list.extend(responseA.get('results'))
    places_list = [{'name':places['name'],'type':places['types'][0]} for places in places_list if places['types'][0] in points_of_interest]#,'loc':places['geometry']['location']
    return places_list
def quantifying_adjective(place):
    if place[1] > 0 and place[1] <= 3:
        return "a "+place[0]
    elif place[1] <= 5:
        return "some "+place[0]+"s"
    elif place[1] > 5:
        return "a lot of "+place[0]+"s"

### location ###
try:
    responseC = map_client.reverse_geocode(latlng=(lat, lng), language='en')
except Exception as error:
    print('[',colored('ERROR','red'),'] reverse geocode (google maps) :', error)
    address = ""
else:
    print('[',colored('OK','green'),'] reverse geocode (google maps)')
    isLocated = False
    for i in range(len(responseC)):
        addr = responseC[i]['address_components']
        addr = {val['types'][0]:val['long_name'] for val in addr}
        if 'country' in addr.keys():
            isLocated = True
            break
    if isLocated:
        if 'locality' in addr.keys():
            try:
                isListed, pop = get_city_wikidata(addr['locality'], addr['country'])
            except Exception as error:
                print('[', colored('ERROR', 'red'), '] city wikidata :', error)
                isListed = False
            else:
                print('[', colored('OK', 'green'), '] city wikidata')
            if isListed:
                area = None
                if 50000 < pop and pop < 250000:
                    area = 'city'
                elif 1500 < pop and pop < 50000:
                    area = 'small city'
                elif 250 < pop and pop < 1500:
                    area = 'village'
                elif pop < 250:
                    area = 'small village'
                elif 'route' in addr.keys():
                    address = f'in {addr["route"]}, {addr["locality"]}, {addr["country"]}'
                else:
                    address = f'in {addr["locality"]}, {addr["country"]}'
                if area:
                    if 'administrative_area_level_1' in addr.keys():
                        address = f'in a {area} in {addr["administrative_area_level_1"]}, {addr["country"]}'
                    else:
                        address = f'in a {area} in {addr["country"]}'
                cityInfo = True
            else:
                cityInfo = False
        else:
            cityInfo = False
    else:
        address = ''
        cityInfo = False
    if not cityInfo and 'administrative_area_level_1' in addr.keys():
        address = f'in {addr["administrative_area_level_1"]}, {addr["country"]}'
    elif not cityInfo:
        address = f'far from the city, in {addr["country"]}'
### location ###

### weather and date ###
url = f"api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={weatherApi_key}&units=metric"
try:
    responseD = json.loads(http.request("GET", url).data)
except Exception as error:
    print('[',colored('ERROR','red'),'] openweathermap :', error)
    hour = "in the day"
    weather = "sunny"
else:
    print('[',colored('OK','green'),'] openweathermap')
    weather = responseD['weather'][0]['description']
    date = datetime.fromtimestamp(responseD['dt']).strftime("%d %B %Y")
    t, t_sunrise, t_noon, t_sunset = responseD['dt'],responseD['sys']['sunrise'], (responseD['sys']['sunrise']+responseD['sys']['sunset'])/2, responseD['sys']['sunset']
    hourThreshold = 2700
    if abs(t_sunrise - t) < hourThreshold:
        hour = "at the sunrise"
    elif t_sunrise + hourThreshold < t and t < t_noon - hourThreshold:
        hour = "during the morning"
    elif abs(t_noon - t) < hourThreshold:
        hour = "at noon"
    elif t_noon + hourThreshold < t and t < t_sunset - hourThreshold:
        hour = "during the afternoon"
    elif abs(t_sunset - t) < hourThreshold:
        hour = "at the sunset"
    elif t > t_sunset or t < t_sunrise:
        hour = "during the night"
### weather and date ###

### places nearby ###
try:
    places_list = []
    for i in range(4): # 20 40 80 160
        places_list.extend(get_places(2**(i+1)*10))
except Exception as error:
    print('[',colored('ERROR','red'),'] places nearby (google maps) :', error)
else:
    print('[',colored('OK','green'),'] places nearby (google maps)')
places_count = {places['type']: 0 for places in places_list}
for places in places_list:
    places_count[places['type']] += 1

places = sorted(places_count.items(), key=lambda x:x[1], reverse=True)
places = [quantifying_adjective(place) for place in places]
if len(places_count) == 0:
    places_nearby = ''
elif len(places_count) == 1:
    places_nearby = f' Nearby we can find {places[0]}.'
else:
    places = places[:len(places)//3+1]
    places_nearby = f' Nearby we can find {", ".join(places)}.'
### places nearby ###

prompt = f'''photo taken {hour} {address}. The weather is {weather}.{places_nearby} The date is {date}'''
print(colored(prompt, "yellow"))
#stop
if input('\ngenerate image ? (y/n)') == 'y':
    url = "https://stablediffusionapi.com/api/v3/text2img"
    payload = json.dumps({
        "key": imgGen_key,
        "prompt": prompt,
        "negative_prompt": None,
        "width": 1024,
        "height": pics_format,
        "samples": 4,
        "num_inference_steps": 40,
        "seed": None,
        "guidance_scale": 7.5,
        "safety_checker": None,
        "upscale": "yes",
        "webhook": None,
        "track_id": None
    })
    headers = {'Content-Type': 'application/json'}
    timeStamp = int(time.time())
    responseE = json.loads(requests.request("POST", url, headers=headers, data=payload).text)
    country = addr['country'] if isLocated else None
    if responseE["id"] == "":
        print(responseE)
        raise SystemExit

    print(f'\"{responseE["id"]}\":[{timeStamp}, \"{country}\", \"{prompt}\"]')
    generatingStatus, urls = pics.get_url(responseE['id'], imgGen_key, 10)

    try:
        with open('failed_downloads.json', 'r') as file:
            failed_downloads = json.load(file)
    except FileNotFoundError:
        with open('failed_downloads.json', 'w+') as file:
            file.write("{}")
            failed_downloads = json.load(file)
    country = addr['country'] if isLocated else None

    if generatingStatus == 'success':
        downloadStatus = pics.download(urls, parent_dir, timeStamp, prompt, country)
    elif generatingStatus == 'processing':
        failed_downloads[responseE['id']] = [timeStamp, country, prompt]
        with open('failed_downloads.json', 'w') as file:
            json.dump(failed_downloads, file)
        print('[',colored('TIMEOUT','orange'),f'] ({responseE["id"]}) images will be downloaded on next run')
    else:
        print('images can\'t be generated')

    for failed_download in failed_downloads.copy().items():
        id, [date, country, prompt] = failed_download
        print(f'\ntrying to download {id} : ', end="")
        generatingStatus, urls = pics.get_url(id, imgGen_key, 1)
        if generatingStatus == 'error':
            del failed_downloads[id]
            print(colored('generation failed','red'))
        elif generatingStatus == 'success':
            downloadStatus = pics.download(urls, parent_dir, date, prompt, country)
            if downloadStatus:
                del failed_downloads[id]
    with open('failed_downloads.json', 'w') as file:
        json.dump(failed_downloads, file)