# -*- coding: utf-8 -*-

# Standard library imports
import os
import sys
import argparse
from pathlib import Path

# Third party imports
import pandas as pd
import geopandas as gpd
import rasterio

def sample_vector_from_raster(raster_path: str|Path, vector_path: str|Path, vector_primary_key: str) -> gpd.GeoDataFrame:
	"""
	Sample raster values from a vector file.
	
	Parameters:
		raster_path (str|Path): Path to the raster file.
		vector_path (str|Path): Path to the vector file.
	
	Returns:
		gpd.GeoDataFrame: A GeoDataFrame with the sampled values.
	"""
	# Read the vector file
	vector = gpd.read_file(vector_path)

	# Check if the vector file has a primary key
	if vector_primary_key not in vector.columns:
		raise ValueError(f"Primary key {vector_primary_key} not found in the vector file.")

	# Open the raster file
	with rasterio.open(raster_path) as src:
		# Initialize the dataframe to store the values. The primary key is the index. All raster bands are columns.
		df = pd.DataFrame(index=vector[vector_primary_key])
		# Loop through the raster bands
		for i in range(src.count):
			# Read the raster band
			band = src.read(i+1)
			# Sample the raster values
			values = [x[0] for x in src.sample(vector.geometry)]
			# Store the values in the dataframe
			df[i] = values

	# Merge the values with the vector file
	vector = vector.merge(df, left_on=vector_primary_key, right_index=True)

	return vector