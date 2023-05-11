import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import seaborn as sns
from copy import deepcopy
import random

import scipy.stats as st
from scipy.stats import pearsonr
import statsmodels.api as sm
import statsmodels.formula.api as smf

from grade_to_number import *

import datetime
from dateutil import parser
import time


def recreate_full_dataset():
	tick_lists = glob("user_ticks/*")
	total_ticks = 0

	df_full = pd.DataFrame()

	for i, tick_list in enumerate(tick_lists):
		if i % 1000 == 0:
			print(i)
		df = pd.read_csv(tick_list)
		if len(df) < 50:
			continue
		df["tick_file"] = tick_list
		total_ticks += len(df)

		df_full = pd.concat([df_full, df], axis=0)

	print("Total ticks processed: ", total_ticks)
	print(len(df_full))
	print(df_full.head())

	df_full["rating_num"] = df_full["Rating Code"] / 100
	df_full.to_csv("df_full_tick_data.csv", index=False)
	return None

def get_statistics():
	tick_lists = glob("user_ticks/*")
	global_tick_count = 0
	sport_count = 0
	trad_count = 0
	boulder_count = 0
	for i, user in enumerate(tick_lists):
		df = pd.read_csv(user)
		if len(df) > 200:
			v = df["Route Type"].value_counts()
			if "Trad" in v.keys():
				trad_count += v["Trad"]
			if "Sport" in v.keys():
				sport_count += v["Sport"]
			if "Boulder" in v.keys():
				boulder_count += v["Boulder"]
			global_tick_count += len(df)

	print("Global tick count: ", global_tick_count)
	print("Trad count: ", trad_count)
	print("Sport count: ", sport_count)
	print("Boulder count: ", boulder_count)

def dict_insert(d, key):
	if key in d:
		d[key] += 1
	else:
		d[key] = 1

def df_to_approved_crags(df_trad, min_crag_size=500):
	d = {}
	# These are the states that don't have subregions, they just go straight to crags,
	# so we want to grab the second thing in the X > Y > Z place name as
	# opposed to the third
	single_states = ["California", "New York", "Kentucky", "New Hampshire",
					 "Wyoming", "South Dakota", "West Virginia", "Georgia", "Tennessee",
					 "Illinois", ]
	locations = []
	for location in df_trad["Location"].values:
		tree = location.split(">")
		if tree[0] == "International " or tree[0] == "* In Progress " or len(tree) <= 2:
			locations.append("SKIP")
			continue
		if tree[0][:-1] in single_states:
			dict_insert(d, tree[1])
			locations.append(tree[1])
		else:
			dict_insert(d, tree[2])
			locations.append(tree[2])

	# Kill all crags that don't have at least 500 associated ticks
	keys_to_del = []
	for k in d:
		if d[k] < min_crag_size:
			keys_to_del.append(k)

	for k in keys_to_del:
		d.pop(k, None)

	df_new = deepcopy(df_trad)
	df_new["crag"] = locations
	return d, keys_to_del, df_new

def df_to_sandbag_list(df):
	sandbag_list = []
	for crag, df_crag in df.groupby("crag"):
		df_crag["rating_gap"] = (df_crag['rating_num'] - df_crag['your_rating_adjusted'])
		total = len(df_crag)
		soft_count, hard_count, exact_count = 0.,0.,0.
		for i, row in df_crag.iterrows():
			if row["rating_gap"] > 0:
				soft_count += 1
			elif row["rating_gap"] < 0:
				hard_count += 1
			else:
				exact_count += 1
		sandbag_list.append([crag, df_crag["rating_gap"].mean(), soft_count / total, hard_count / total, exact_count / total])
	return sandbag_list

def process_row(d, x):
	adjusted_x = x["Your Rating"].split()[0]
	if adjusted_x not in d.keys():
		return "NONE"
	return float(d[adjusted_x]) / 100.

def get_ratings_without_modifiers(df, grade_dict):
	adj_ratings = []
	for rating in df["Rating"].values:
		k = rating
		if (len(rating.split(" ")) > 1) and (rating.split(" ")[-1] in "RPG13X"):
			k = " ".join(rating.split(" ")[:-1])
		if k in grade_dict.keys():
			adj_rating = grade_dict[k]
		else:
			adj_rating = "NONE"
		adj_ratings.append(adj_rating)
	return adj_ratings


# This is currently broken
def analyze_user_given_ratings(df_loaded):

	# this is currently ruined b/c the new grade dict is being used but need
	# the old one for this analysis
	df_with_ratings = df_loaded.dropna(subset=["Your Rating"])
	df_sport_with_ratings = df_with_ratings[df_with_ratings["Route Type"] == "Sport"]
	df_trad_with_ratings = df_with_ratings[df_with_ratings["Route Type"] == "Trad"]

	d_final = get_grade_to_number_dict()
	print(d_final)

	df_sport_with_ratings["your_rating_adjusted"] = df_sport_with_ratings.apply(lambda x: process_row(d, x), axis=1)
	df_trad_with_ratings["your_rating_adjusted"] = df_trad_with_ratings.apply(lambda x: process_row(d, x), axis=1)


	print("NONE" in set(df_sport_with_ratings["your_rating_adjusted"].values))
	print("NONE" in set(df_trad_with_ratings["your_rating_adjusted"].values))

	df_sport_with_ratings_adjusted = df_sport_with_ratings[df_sport_with_ratings.apply(lambda x: x["your_rating_adjusted"] != "NONE", axis=1)]
	df_trad_with_ratings_adjusted = df_trad_with_ratings[df_trad_with_ratings.apply(lambda x: x["your_rating_adjusted"] != "NONE", axis=1)]

	assert ("NONE" not in set(df_sport_with_ratings_adjusted["your_rating_adjusted"].values))
	assert ("NONE" not in set(df_trad_with_ratings_adjusted["your_rating_adjusted"].values))

	d_s, keys_to_del_s, new_df_sport = df_to_approved_crags(df_sport_with_ratings_adjusted)
	d_t, keys_to_del_t, new_df_trad = df_to_approved_crags(df_trad_with_ratings_adjusted)
	approved_sport_locations = list(d_s.keys())
	approved_trad_locations = list(d_t.keys())

	df_sport_final = new_df_sport[
		new_df_sport.apply(lambda x: x['crag'] in approved_sport_locations, axis=1)]
	df_trad_final = new_df_trad[
		new_df_trad.apply(lambda x: x['crag'] in approved_trad_locations, axis=1)]

	sport_sandbag_list = df_to_sandbag_list(df_sport_final)
	trad_sandbag_list = df_to_sandbag_list(df_trad_final)

	trad_sandbag_list.sort(key=lambda x: x[1], reverse=True)
	sport_sandbag_list.sort(key=lambda x: x[1], reverse=True)

	return trad_sandbag_list, sport_sandbag_list


def create_final_df_regression(df_loaded, output_path="trad_data_df_final.csv", climb_type="Trad", num_routes_cutoff=200, num_hard_routes_cutoff=20):
	df_trad = df_loaded.loc[df_loaded['Route Type'] == climb_type]
	df_trad.dropna(subset=["Rating"], inplace=True)
	df_trad["adj_rating"] = get_ratings_without_modifiers(df_trad, get_grade_to_number_dict())
	d, keys_to_del, df_trad = df_to_approved_crags(df_trad)
	approved_locations = list(d.keys())

	df_trad_adjusted = df_trad[df_trad.apply(lambda x: ((x["crag"] in approved_locations) and (x["adj_rating"] is not "NONE")), axis=1)]
	df_trad_adjusted = df_trad_adjusted.where(pd.notnull(df_trad_adjusted), "None")

	routes_by_area = {}
	hard_routes_by_area = {}
	for _, row in df_trad_adjusted.iterrows():
		if row["crag"] in routes_by_area.keys():
			routes_by_area[row["crag"]].add(row["Route"])
		else:
			routes_by_area[row["crag"]] = set([row["Route"]])

		if row["crag"] in hard_routes_by_area.keys():
			if row["rating_num"] >= 26.:
				hard_routes_by_area[row["crag"]].add(row["Route"])
		else:
			if row["rating_num"] >= 26.:
				hard_routes_by_area[row["crag"]] = set([row["Route"]])

	above_200_count, above_20_count = 0, 0
	new_approved_crags = []
	for area in routes_by_area:
		if len(routes_by_area[area]) > num_routes_cutoff:
			if len(hard_routes_by_area[area]) > num_hard_routes_cutoff:
				new_approved_crags.append(area)

	df_trad_final = df_trad_adjusted[df_trad_adjusted.apply(lambda x: x["crag"] in new_approved_crags, axis=1)]
	print("BEFORE CUT: ", df_trad_final.columns)
	print(df_trad_final.shape)
	df_regression = df_trad_final[["rating_num", "tick_file", "crag", "Style", 'Lead Style', 'Length', 'Avg Stars', "adj_rating", "Location", "Route"]]
	print("AFTER: ", df_regression.shape)
	print(df_regression.columns)
	df_regression = df_regression.rename(columns={"Lead Style": "lead_style", "Avg Stars": "avg_stars"})

	df_regression_final = df_regression.dropna()

	df_regression_final["rating_num"] = pd.to_numeric(df_regression_final["rating_num"])
	df_regression_final["avg_stars"] = pd.to_numeric(df_regression_final["avg_stars"])
	df_regression_final.drop("Length", axis=1)

	df_regression_final.to_csv(output_path, index=False)
	return df_regression_final, approved_locations

def perform_regression_analysis(input_path):
	df_regression_final = pd.read_csv(input_path)
	df_regression_final = df_regression_final.sample(frac = 1)
	t1 = time.time()
	# DIVYA -- this is the line where I can't push the size up to the full dataset size (~600k)
	# adj_rating is the grade of the climb, tick_file is the name of the climber, crag is the climbing area,
	# Style is whether they led or followed the climb, lead style is whether they
	# onsighted, redpointed, pinkpointed, etc.
	# I can't push this much past 200k on my local machine. even if i could parallelize that'd be huge
	lsdv_model = smf.ols(formula="adj_rating~tick_file + crag + Style + lead_style",
			data=df_regression_final[:200000])
	lsdv_model_results = lsdv_model.fit()
	t2 = time.time()
	print(t2 - t1)
	print('===============================================================================')
	print('============================== OLSR With Dummies ==============================')
	print(lsdv_model_results.summary())
	print('LSDV='+str(lsdv_model_results.ssr))
	return lsdv_model_results

def avg_dev_per_area(user_df, area, global_sandbag_dict):
	running_avg = 0
	avg_dev, ad_count, row_counter = 0, 0, 0
	for i, row in user_df.iterrows():
		dev = row["adj_rating"] - running_avg
		full_climb_name = row["Location"] + row["Route"]
		if full_climb_name in global_sandbag_dict:
			global_sandbag_dict[full_climb_name] += dev
		else:
			global_sandbag_dict[full_climb_name] = dev
		if row["crag"] == area:
			avg_dev += dev
			ad_count += 1
		running_avg = ((running_avg * row_counter) + row["adj_rating"]) / (row_counter + 1.0)  # UPDATE
		row_counter += 1
	if ad_count == 0:
		return None
	#print("This: ", avg_dev, ad_count)
	return (avg_dev / ad_count)

def climber_average_deviations(approved_crags, df):
	# TODO: FIX NANS SHOWING UP
	global_sandbag_dict = {}
	print("Number of crags: ", len(approved_crags))
	print("Number of users: ", len(set(df["tick_file"].values)))
	results = []
	for crag in approved_crags:
		print("Doing crag: ", crag)
		dev_vals = []
		grouped = df.groupby(["tick_file"])
		
		c = 0
		# this could all be done more efficiently but whatever
		for user in set(df["tick_file"].values):
			c += 1
			df_usr = grouped.get_group(user)
			val = avg_dev_per_area(df_usr, crag, global_sandbag_dict)
			if val:
				dev_vals.append(val)
		if len(dev_vals) == 0:
			print("No users had data for this crag.")
			continue
		avg_dev = np.mean(dev_vals)
		print(crag, avg_dev, len(dev_vals))
		results.append([crag, avg_dev, len(dev_vals)])
	results.sort(key=lambda x: x[1], reverse=False)
	return results, global_sandbag_dict



def main():
	df_loaded = pd.read_csv("df_full_tick_data.csv", delimiter=",", lineterminator='\n')
	
	# currently broken
	#t,s = analyze_user_given_ratings(df_loaded)

	#create_final_df_regression(df_loaded, output_path="trad_data_df_final.csv", climb_type="Trad")
	#perform_regression_analysis("trad_data_df_final.csv")

	# df_sport, approved_locations = create_final_df_regression(df_loaded, output_path="sport_data_df_final.csv",
	# 		climb_type="Sport", num_routes_cutoff=400, num_hard_routes_cutoff=40)
	df_trad, approved_locations = create_final_df_regression(df_loaded, output_path="trad_data_df_final.csv",
			climb_type="Trad", num_routes_cutoff=200, num_hard_routes_cutoff=20)
	print(len(df_trad), len(approved_locations))
	df_trad.dropna()

	perform_regression_analysis("trad_data_df_final.csv")

	#df_sport = pd.read_csv("sport_data_df_final.csv")
	#d, keys_to_del, df_new = df_to_approved_crags(df_sport, min_crag_size=500)

	# results, sandbag_dict = climber_average_deviations(approved_locations, df_trad)
	# print(results)
	# sandbag_dict_list = [(k,v) for k, v in sandbag_dict.items()]
	# sandbag_dict_list.sort(key=lambda x: x[1], reverse=False)
	# print(sandbag_dict_list[:20], sandbag_dict_list[-20:])

if __name__ == "__main__":
	main()


