# -*- coding: utf-8 -*-

# NOTES FOR BK
# Make yml: conda env export | grep -v "^prefix: " > environment.yml

# Standard library imports
from datetime import datetime
from json import loads
from pathlib import Path

# Third party imports
import geopandas as gpd
import pandas as pd
import rasterio as rio


class SampleVectorFromRaster:

    @classmethod
    def sample(self, varname: str, geometry_path: str, start_date: str, end_date: str) -> gpd.GeoDataFrame:
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
                "variable": {
                    "<varname: str>": {
                        "dirpath": "<raster_dir_path: str>"
                        "filename_mask": ".*_.*_.*_.*_[YEAR]_[DOY]_[HOUR].tif"
                        "nan_value": -9999
                    }
                }
            }

        """
        # load config files
        with open("config.json", "r") as f: config = loads(f.read())

        # assert that varname is in config.varnames
        assert varname in config["variable"].keys(), f"Variable {varname} not found in config file. Valid variables are: {config['variable'].keys()}"

        # prepare sampling vector file
        try: gdf = gpd.read_file(geometry_path)
        except Exception as e: raise Exception(f"Error reading geometry file: {e}")
        gdf.dropna(subset=["geometry"], inplace=True) # optional: drop rows with missing geometries

        # start_date and end_date to DateTime objects (YYYYMMDDD)
        start_date = datetime.strptime(start_date, "%Y%m%d")
        end_date = datetime.strptime(end_date, "%Y%m%d")

        # get all raster files in the directory in the time period
        print(f"Starting sampling for variable '{varname}' in time period {start_date} to {end_date}...")
        raster_dir = Path(config["variable"][varname]["dirpath"])
        raster_files = [x for x in raster_dir.iterdir() if x.suffix == ".tif"]

        # filter raster files by time period (start_date (year and doy, included) and end_date (year and doy, included))
        raster_files_selection = []
        for raster_file in raster_files:
            try:
                raster_file_year = int(raster_file.stem.split("_")[4])
                raster_file_doy = int(raster_file.stem.split("_")[5])
                if start_date <= datetime(raster_file_year, 1, 1) + pd.Timedelta(days=raster_file_doy) <= end_date:
                    raster_files_selection.append(raster_file)
            except Exception as e: 
                print(f"[WARNING]: Error occurred with raster file. Error: {e} Path: {raster_file} Continuing...")
                continue
        raster_files_selection = sorted(raster_files_selection, key=lambda x: datetime.strptime(x.stem.split("_")[4] + x.stem.split("_")[5] + x.stem.split("_")[6], "%Y%j%H")) # sort raster files by datetime
        print(f"\nRaster files selected: {len(raster_files_selection)}. \nEarliest: {raster_files_selection[0]}. \nLatest:   {raster_files_selection[-1]}\n")

        # sample raster values for each raster file
        df_list = []
        print(f"Sampling {gdf.shape[0]} points from {len(raster_files_selection)} raster files...")
        for raster_file in raster_files_selection:
            print(f"Sampling raster values from {str(raster_file)}...", end=" ")
            df = self._d2r_sampling(raster_file, gdf, config["variable"][varname]["nan_value"])
            print("Done.")
            df_list.append(df)

        # concatenate all the sampled values
        final_df_concat = pd.concat(df_list, ignore_index=True, axis=0)
        print(f"\n---\nSampling complete. Final DataFrame shape: {final_df_concat.shape}.\nHead:\n{final_df_concat.head()}\n")
        
        return final_df_concat

    @classmethod
    def _d2r_sampling(self, raster_path: Path, multipoint_gdf: gpd.GeoDataFrame, nan_value : int=-9999) -> pd.DataFrame:
        """
        Sample raster values from a multipoint file.
        Specific to the D2R project, not intended for general use.
        
        Parameters:
            raster_path (str|Path): Path to the raster file.
            multipoint_path (str|Path): Path to the multipoint file.
            new_column_name (str): Name of the new column to be created in the GeoDataFrame. 
                                This should be descriptive of the raster values being sampled.
        
        Returns:
            gpd.GeoDataFrame: A GeoDataFrame with the sampled values.

        Data structure of the GeoDataFrame:
            | datetime             | varname | val  | filepath            |
            |----------------------|---------|------|---------------------|
            | 2024-08-01T00:00:00Z | UTCI    | 30.0 | /path/to/raster.tif |
            | 2024-08-01T00:00:00Z | UTCI    | 31.0 | /path/to/raster.tif |
            | 2024-08-01T00:00:00Z | UTCI    | 32.0 | /path/to/raster.tif |
            | 2024-08-01T00:00:00Z | UTCI    | 33.0 | /path/to/raster.tif |
            | 2024-08-01T00:00:00Z | UTCI    | 34.0 | /path/to/raster.tif |
        """
        # create a new dataframe to store the sampled values
        final_df = pd.DataFrame(index=range(len(multipoint_gdf)))
        final_df["lantern_id"] = multipoint_gdf["LeuchtenNr"]
        final_df["datetime"] = datetime.strptime(raster_path.stem.split("_")[4] + raster_path.stem.split("_")[5] + raster_path.stem.split("_")[6], "%Y%j%H").isoformat() + "Z"
        final_df["varname"] = raster_path.stem.split("_")[0]
        # read raster file
        with rio.open(raster_path) as src:
            # sample raster values
            coord_list = [(x, y) for x, y in zip(multipoint_gdf.geometry.x, multipoint_gdf.geometry.y)]
            final_df["val"] = [x for x in src.sample(coord_list)]
            final_df["val"] = final_df["val"].astype(float)

            # check for nan values (default determined by arg) and print sum warning
            nan_values = final_df[final_df["val"] == nan_value]
            if len(nan_values) > 0:
                print(f"\n[WARNING]: Found {len(nan_values)} NaN values in raster file '{raster_path}'. No action taken - continuing...", end=" ")

        final_df["filepath"] = str(raster_path)

        return final_df
    
    @classmethod
    def _generic_sampling(self, raster_path: str, vector_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
        """
        Generic sampling function to sample raster values from a vector file.

        Parameters:
            raster_path (str): Path to the raster file.
            vector_gdf (gpd.GeoDataFrame): GeoDataFrame with the vector data.

        Returns:
            pd.DataFrame: DataFrame with the sampled values.

        Data structure of the DataFrame:
            | val    |
            |--------|
            | [30.0] |
            | [31.0] |
            | [32.0] |
        """
        final_df = pd.DataFrame(index=range(len(vector_gdf)))
        with rio.open(raster_path) as src:
            coord_list = [(x, y) for x, y in zip(vector_gdf.geometry.x, vector_gdf.geometry.y)]
            final_df["val"] = [x for x in src.sample(coord_list)]
        
        # if shape is bigger than 1, warning
        if len(final_df) > 1:
            print(f"\n[INFO]: Found {len(final_df)} values in multiband raster file '{raster_path}'. No action taken - continuing...", end=" ")
        
        return final_df


if __name__ == "__main__":

    df_utci = SampleVectorFromRaster.sample("UTCI", "/home/kraasbx5/network_loc_20240405.geojson", "20240801", "20240801")
    df_mrt = SampleVectorFromRaster.sample("MRT", "/home/kraasbx5/network_loc_20240405.geojson", "20240801", "20240801")
    df_concat = pd.concat([df_utci, df_mrt], ignore_index=True, axis=0)
    df_concat.to_csv("output.csv", index=False)
