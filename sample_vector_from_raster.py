# -*- coding: utf-8 -*-

# Standard library imports
from pathlib import Path

# Third party imports
import geopandas as gpd
import pandas as pd
import rasterio as rio
import matplotlib.pyplot as plt
from shapely.geometry import Point

def sample_vector_from_raster(raster_path: str|Path, multipoint_path: str|Path, multipoint_primary_key: str) -> gpd.GeoDataFrame:
	"""
	Sample raster values from a vector file.
	
	Parameters:
		raster_path (str|Path): Path to the raster file.
		multipoint_path (str|Path): Path to the vector file.
		vector_primary_key (str): The primary key of the vector file.
	
	Returns:
		gpd.GeoDataFrame: A GeoDataFrame with the sampled values.
	"""
	# Check if the vector file has a primary key
	if multipoint_primary_key not in vector.columns:
		raise ValueError(f"Primary key {multipoint_primary_key} not found in the vector file.")
	
	# Read the vector file
	vector = gpd.read_file(multipoint_path)

	points = [ # Placeholder
		Point(625466, 5621289),
		Point(626082, 5621627),
		Point(627116, 5621680),
		Point(625095, 5622358),
	]
	gdf = gpd.GeoDataFrame([1, 2, 3, 4], geometry=points, crs=32630)
	coord_list = [(x, y) for x, y in zip(gdf["geometry"].x, gdf["geometry"].y)]

	# Read the raster file
	src = rio.open(raster_path)

	# Open the raster file
	with rio.open(raster_path) as src:
		# Initialize the dataframe to store the values. The primary key is the index. All raster bands are columns.
		df = pd.DataFrame(index=vector[multipoint_primary_key])

		# Loop through the raster bands
		for i in range(src.count):
			# Sample the raster values and store the values in the dataframe
			df[i] = [x[0] for x in src.sample(vector.geometry)]

			df[i] = [x for x in src.sample(coord_list)]

	# Merge the values with the vector file
	# Will this change the file?
	vector = vector.merge(df, left_on=multipoint_primary_key, right_index=True)

	return vector