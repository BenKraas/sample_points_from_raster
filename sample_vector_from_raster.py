# -*- coding: utf-8 -*-

# NOTES FOR BK
# Make yml: conda env export | grep -v "^prefix: " > environment.yml

# Standard library imports
from pathlib import Path

# Third party imports
import geopandas as gpd
import pandas as pd
import rasterio as rio
from datetime import datetime
from json import loads


def main_sampling(varname: str, geometry_path: str, start_date: str, end_date: str) -> gpd.GeoDataFrame:
	"""
	Sample raster values from a vector file to a GeoDataFrame.
	Tailored to D2R project file structure, where raster files are accessed by the script.
	
	Parameters:
		varname (str): Name of the variable to sample.
		geometry_path (str): Path to the vector file.
		start_date (str): Start date of the time period to sample.
		end_date (str): End date of the time period to sample.
		
	Returns:
		gpd.GeoDataFrame: A GeoDataFrame with the sampled values.

	Example:
		main_sampling("varname", "path/to/geometry_file", "YYYYMMDD", "YYYYMMDD")

	Layout of config.json:
		{
			"<variable: str>": {
				"varname": {
					"dirpath": "<raster_dir_path: str>"
					"filename_mask": "UTCI_pytherm_3m_v0.6.0_[YEAR]_[DOY]_[HOUR].tif"
				}
			}
		}

	"""
	# load config files
	with open("config.json", "r") as f: config = loads(f.read())

	# assert that varname is in config.varnames
	assert varname in config["variable"].keys(), f"Variable {varname} not found in config file."

	# prepare sampling vector file
	try: gdf = gpd.read_file(geometry_path)
	except Exception as e: raise Exception(f"Error reading geometry file: {e}")
	gdf.dropna(subset=["geometry"], inplace=True) # optional: drop rows with missing geometries

	# start_date and end_date to DateTime objects (YYYYMMDDD)
	start_date = datetime.strptime(start_date, "%Y%m%d")
	end_date = datetime.strptime(end_date, "%Y%m%d")

	# get all raster files in the directory in the time period
	raster_dir = Path(config["variable"][varname]["dirpath"])
	raster_files = [x for x in raster_dir.iterdir() if x.suffix == ".tif"]

	# filter raster files by time period (start_date (year and doy, included) and end_date (year and doy, included))
	raster_files = [x for x in raster_files if start_date <= datetime.strptime(x.stem.split("_")[2], "%Y%j%H") <= end_date]

	# sample raster values for each raster file
	df_list = []
	for raster_file in raster_files:
		df = sample_from_raster(raster_file, gdf, raster_file.stem)
		df_list.append(df)

	# concatenate all the sampled values
	final_df_concat = pd.concat(df_list, ignore_index=True, axis=0)
	
	return final_df_concat



def sample_from_raster(raster_path: Path, multipoint_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
	"""
	Sample raster values from a multipoint file.
	
	Parameters:
		raster_path (str|Path): Path to the raster file.
		multipoint_path (str|Path): Path to the multipoint file.
		new_column_name (str): Name of the new column to be created in the GeoDataFrame. 
							   This should be descriptive of the raster values being sampled.
	
	Returns:
		gpd.GeoDataFrame: A GeoDataFrame with the sampled values.
	"""
	# read raster file
	with rio.open(raster_path) as src:
		raster = src.read(1)
		meta = src.meta

	# sample raster values
	# get the values of the raster at the points
	# the points are in the geometry column of the GeoDataFrame
	# the values are stored in the new column
	multipoint_gdf["val"] = [x[0] for x in src.sample(multipoint_gdf.geometry)]

	# populate the dataframe with the datetime of the raster file, the raster path
	final_df = pd.DataFrame(index=range(len(multipoint_gdf)))
	final_df["datetime"] = datetime.strptime(raster_path.stem.split("_")[4] + raster_path.stem.split("_")[5] + raster_path.stem.split("_")[6], "%Y%j%H").isoformat() + "Z"
	final_df["raster_path"] = raster_path
	final_df["val"] = multipoint_gdf["val"]

	return final_df
	

if __name__ == "__main__":
	# save as .csv
	main_sampling("varname", 
			      "path/to/geometry_file", 
				  "YYYYMMDD", 
				  "YYYYMMDD").to_csv("output.csv", index=False)