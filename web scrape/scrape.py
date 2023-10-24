import requests
from bs4 import BeautifulSoup
import json
import time


BASE_URL = "https://www.airnav.com"
URL = "https://www.airnav.com/airports/us"
'''
page = requests.get(URL)
if not page.ok:
    print("Error getting base page")
soup = BeautifulSoup(page.content, "html.parser")

with open("all_states.html", "w") as file:
    file.write(str(soup))
'''

localURL = "all_states.html"
page = open(localURL)
soup = BeautifulSoup(page.read(), "html.parser")
page.close()

states = []

i = 0
for a in soup.find_all('a', href=True):
    if a['href'].startswith("/airports/us"):
        i += 1
        if i % 2 == 1:
            states.append(a['href'])


airport_ids = {}

for s in states:
    '''
    page = requests.get(BASE_URL + s)
    if not page.ok:
        print("Error getting state page")
    soup = BeautifulSoup(page.content, "html.parser")

    with open("states/" + s[13:] + ".html", "w") as file:
        file.write(str(soup))
    '''

    page = open("states/" + s[13:] + ".html")
    soup = BeautifulSoup(page.read(), "html.parser")

    for a in soup.find_all('a', href=True):
        if a["href"].startswith("/airport/"):
            a_id = a["href"][9:]
            airport_ids[a_id] = a["href"]

    page.close()


airport_coords = {}
for i in list(airport_ids.keys()):
    print(i)
    page = requests.get(BASE_URL + airport_ids[i])

    if page.ok:
        soup = BeautifulSoup(page.content, "html.parser")

        airport_coords[i] = soup.find_all("td", string="Lat/Long: ")[0].find_next_sibling("td").find_all("br")[-2].nextSibling

        with open('coordinates.json', 'w', encoding='utf-8') as f:
            json.dump(airport_coords, f, ensure_ascii=False, indent=4)
        
        time.sleep(5)

    else:
        print("Error getting airport page")
        break
