from glob import glob
import time
import wget
import os

files = glob("*_user_links.txt")

user_links = []
for f in files:
	fo = open(f, "r")
	for l in fo:
		user_links.append(l.strip())
	fo.close()
user_links = list(set(user_links))
print(user_links[:10])
print("Number of unique users: ", len(user_links))

t1 = time.time()
for q, link in enumerate(user_links):
	if q % 25 == 0:
		print("Processed user number: ", q)
		t2 = time.time()
		print("time elapsed for 25 users: ", t2 - t1)
		t1 = time.time()
	output_path = "user_ticks/" + link.split("/")[-1] + "_ticks.csv"
	if os.path.exists(output_path):
		continue
	try:
		wget.download(link + "/tick-export")
	except:
		print("Errored out on link: ", link)
		continue
	if os.path.exists("ticks.csv"):
		os.rename("ticks.csv", output_path)