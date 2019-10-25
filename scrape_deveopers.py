import requests
from bs4 import BeautifulSoup
page = requests.get("https://github.com/trending/developers")
soup = BeautifulSoup(page.content, 'html.parser')
users = []
for i in list(soup.find_all('article', {"class": "Box-row d-flex"})):
	#print(i.find('div', {"class": "mx-3"})) #foto
	user = i.find('div', {"class": "d-sm-flex flex-auto"}).find('div', {"class": "col-sm-8 d-md-flex"}).find('div', {"class": "col-md-6"}).find('h1', {"class": "h3 lh-condensed"})
	user_info = {}
	
	user_info['link'] = "https://github.com" + user.find('a')['href']
	user_info['nome'] = user.find('a').get_text().replace("\n", "").replace('/[ ]{2}/g', "")
	user_info['id'] = list(soup.find_all('article', {"class": "Box-row d-flex"})).index(i)
	users.append(user_info)

print(users)

