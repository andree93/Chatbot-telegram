class User:
    def __init__(self, name):
        self.name = name
        self.id = id
        self.query = Query()

class Query:
    def __init__(self, radius=None, placeType=None, maxprice=None, latitude=None, longitude=None):
        self.radius = radius
        self.latitude = latitude
        self.longitude = longitude
        self.placeType = placeType
        self.maxprice = maxprice
        self.places = []

class Place:
    def __init__(self, lat, long, place_id, vicinity=None, name=None, rating=None, price_level=None):
        self.name = name
        self.lat = lat
        self.long = long
        self.price_level = price_level
        self.rating = rating
        self.place_id = place_id
        self.vicinity = vicinity