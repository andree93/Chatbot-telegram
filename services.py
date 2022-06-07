from urllib import response
import aiohttp
import asyncio
import requests
from jproperties import Properties
from syncer import sync
from models import Query, Place, User

configs = Properties()
with open('app-config.properties', 'rb') as config_file:
    configs.load(config_file)

API_KEY_GOOGLE = configs.get("API_KEY_GOOGLE").data




def getUrlRequest(lat, lon, placeType="restaurant|bar|food", radius=0):
    if radius == 0:
        return f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat}%2C{lon}&rankby=distance&type={placeType}&opennow=true&key={API_KEY_GOOGLE}"
    else:
        return f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat}%2C{lon}&radius={radius}&type={placeType}&opennow=true&key={API_KEY_GOOGLE}"

def DAO(json): #returns array of "Places" objects
    results = [result for result in json['results']]
    objects_places = [Place(name=obj['name'], lat=obj['geometry']['location']['lat'], long=obj['geometry']['location']['lng'], price_level=obj.get('price_level', "N/A"),rating=obj.get('rating', "N/A"), place_id=obj['place_id'], vicinity=obj.get('vicinity', "N/A")) for obj in results]

    """for obj in objects_places: #test
        print(f"name: {obj.name}") #test
        print(f"price level: {obj.price_level}")  # test
        print(f"rating: {obj.rating}")  # test """
    return objects_places


def getNearbyPlacesSync(lat, lon, placeType="restaurant|bar|food", radius=0):
    urlReq = getUrlRequest(lat=lat, lon=lon, placeType=placeType, radius=0)
    req = requests.get(urlReq)
    if req.status_code == 200:
        return req.json()
    else:
        print("errore richiesta!")


async def getNearbyPlacesAsync(lat, lon, placeType="restaurant|bar|food", radius=0):
    urlReq = getUrlRequest(lat=lat, lon=lon, placeType=placeType, radius=0)
    async with aiohttp.ClientSession() as session:
        async with session.get(urlReq) as response:
            json = await response.json()
            if response.status == 200:
                return json
            else:
                print("errore!")

async def main():
    json = await getNearbyPlacesSync("40.3977429%2C17.4496393")
    DAO(json)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())