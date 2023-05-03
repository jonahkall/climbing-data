import requests
import wget
from bs4 import BeautifulSoup
import os
import pandas as pd
import time

def get_user_urls_from_forum(thread_link):
	page = requests.get(thread_link)
	soup = BeautifulSoup(page.content, "html.parser")
	results = soup.find(id="forum-table")
	if results is None:
		return []
	rows = results.find_all("td", {'class': 'message-avatar text-xs-center hidden-xs-down'})
	user_links = []
	for row in rows:
		for link in row.find_all("a", href=True):
			if "user" in link["href"]:
				user_links.append(link["href"])
	return user_links


def get_ticks_from_forum_url(base_forum_url, name, num_pages, user_link_cache = set([])):
	user_links = []
	for i in range(1, num_pages):
		t1 = time.time()
		forum_url = base_forum_url + "?page=" + str(i)
		page = requests.get(forum_url, timeout=45)
		if page is None:
			continue
		soup = BeautifulSoup(page.content, "html.parser")

		results = soup.find(id="forum-table")

		job_elements = results.find_all("div")
		for elem in job_elements:
			links = elem.find_all("a")
			if "topic" in links[0]["href"]:
				tick_urls = get_user_urls_from_forum(links[0]["href"])
				user_links += tick_urls
		t2 = time.time()
		print("Iteration time: ", t2-t1)

	user_links = list(set(user_links))
	print("Found ", len(user_links), " users.")
	f = open(name + "_user_links.txt", "w")
	for link in user_links:
		f.write(link + '\n')
	f.close()

	return
	
	for q, link in enumerate(user_links):
		if link in user_link_cache:
			continue
		if q % 25 == 0:
			print("User number ", q, " is: ", link)
		wget.download(link + "/tick-export")
		os.rename("ticks.csv", "user_ticks/" + link.split("/")[-1] + "_ticks.csv")

forum_urls = ["https://www.mountainproject.com/forum/103989405/general-climbing",
			  "https://www.mountainproject.com/forum/103989417/climbing-gear-discussion",
			  "https://www.mountainproject.com/forum/103989416/for-sale-for-free-want-to-buy"]
page_nums = [351, 307, 1195] # max number of pages in each forum, set by hand for now which is a little silly
names = ["general", "gear", "free_sale"]
ulc = set()

for i, f in enumerate(forum_urls):
	if i is not 2:
		continue
	get_ticks_from_forum_url(f, names[i], page_nums[i], ulc)
