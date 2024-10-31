# -*- coding: utf-8 -*-

# Standard library imports
from pathlib import Path

# Third party imports
import geopandas as gpd
import rasterio as rio


def sample_vector_from_raster(raster_path: str|Path, multipoint_path: str|Path, new_column_name: str) -> gpd.GeoDataFrame:
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
	raster_path = Path("./data/UTCI_pytherm_3m_v0.6.0_2024_305_15.tif")
	multipoint_path = Path("./data/network_loc_20240405.geojson")

	gdf = sample_vector_from_raster(raster_path, multipoint_path, "UTCI")

	# save the GeoDataFrame to geojson
	gdf.to_file("./data/sample.geojson", driver="GeoJSON")
	