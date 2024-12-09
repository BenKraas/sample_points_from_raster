# -*- coding: utf-8 -*-

# Standard library imports
from pathlib import Path

# Third party imports
import geopandas as gpd
import rasterio as rio
from datetime import datetime
from json import loads


def main_sampling(varname: str, geometry_path: str, start_date: str, end_date: str) -> gpd.GeoDataFrame:
	# load config file
	with open("config.json", "r") as f: config = loads(f.read())

	# assert that varname is in config.varnames
	assert varname in config["varnames"], f"Variable {varname} not found in config file."

	# start_date and end_date to DateTime objects (YYYYMMDDD)
	start_date = datetime.strptime(start_date, "%Y%m%d")
	end_date = datetime.strptime(end_date, "%Y%m%d")

	# get the raster file path
	raster_path = Path(config["raster_dir"]) / f"{varname}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.tif"








def sample_from_raster(raster_path: str|Path, multipoint_path: str|Path, new_column_name: str) -> gpd.GeoDataFrame:
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
	# read the multipoint file
	gdf = gpd.read_file(multipoint_path)
	gdf.dropna(subset=["geometry"], inplace=True) # optional: drop rows with missing geometries

	# read the raster file
	src = rio.open(raster_path)

	# get the coordinates for each point in the multipoint file
	coord_list = [(x, y) for x, y in zip(gdf["geometry"].x, gdf["geometry"].y)]

	# sample the raster values at the coordinates
	gdf[new_column_name] = [x for x in src.sample(coord_list)]

	return gdf
	

if __name__ == "__main__":
	# 
	