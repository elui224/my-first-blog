import requests
import urllib.request
import json

def get_price(): #This functions gets the list of dictionaries from the URL.
    url = 'https://api.coinmarketcap.com/v1/ticker/' 
    # params = {'name': name}
    # response = requests.get(url)
    #response = urllib.request.urlopen(url)
    r = requests.get(url)
    price = r.json()
    return price