"""
Script to launch pysewer computation
"""

import argparse
import importlib.util
import pathlib
import site
import sqlite3
from pathlib import Path
from typing import Optional, cast


def main():
    """Parse command line arguments"""

    parser = argparse.ArgumentParser(description="pysewer")
    parser.add_argument("--yaml", type=str, help="filename")
    parser.add_argument("--check-installed", help="check if pysewer is installed", action="store_true")
    parser.add_argument("--external-libs", type=str, help="optional external libraries directory")
    parser.add_argument("--output-path", type=str, help="output layer path (must be a geopackage)")
    parser.add_argument("--sinks-path", type=str, help="optional sink file path (must be a shapefile)")
    args = parser.parse_args()

    if args.external_libs is not None:
        if Path(args.external_libs).exists():
            site.addsitedir(args.external_libs)
        elif not args.check_installed:
            raise ValueError(f"Path to external libraries {args.external_libs} does not exist")

    if args.check_installed:
        if module_spec := importlib.util.find_spec("pysewer"):
            print(module_spec.origin)
        else:
            print("pysewer is not installed")
        return

    if args.yaml is None:
        raise ValueError("YAML filename not supplied")
    if args.output_path is None:
        raise ValueError("output path not supplied")

    filename = pathlib.Path(args.yaml)
    output_path = pathlib.Path(args.output_path)
    sinks_path = None if args.sinks_path is None else pathlib.Path(args.sinks_path)

    if output_path.suffix != ".gpkg":
        raise ValueError("The output layer path must be a geopackage")
    if sinks_path is not None and sinks_path.suffix != ".shp":
        raise ValueError("The sinks layer path must be a shapefile")

    run(filename, output_path, sinks_path)


def run(filename: pathlib.Path, output_path: pathlib.Path, sinks_path: Optional[pathlib.Path]):
    """Launch pysewer computation"""

    # pylint:disable=import-outside-toplevel,import-error
    import fiona
    import geopandas as gpd
    import pandas as pd
    from pysewer import ModelDomain
    from pysewer.config.settings import load_config
    from pysewer.export import write_gdf_to_gpkg
    from pysewer.helper import get_edge_gdf, get_node_gdf, get_sewer_info
    from pysewer.optimization import calculate_hydraulic_parameters, estimate_peakflow
    from pysewer.routing import rsph_tree
    from rasterio.crs import CRS

    class PysewerToGpkgSpecs:
        """
        Class to transform the GeoDataFrame to our needs for ELAN:
          - remove unwanted columns
          - still create a layer even if the GeoDataFrame is empty
          - handle fid specific field
        """

        layer_name = ""
        geometry = ""
        fields = {}

        def __init__(self, gdf: gpd.GeoDataFrame, crs: CRS):
            self.gdf = gdf
            self.crs = crs

        def write_to_gpkg(self, output_path: str):
            # If no feature in the data frame, export with fiona to export the schema only
            if self.gdf.size == 0:
                properties = self.fields
                properties.update({"fid": "int"})
                with fiona.open(
                    output_path,
                    mode="w",
                    driver="GPKG",
                    layer=self.layer_name,
                    crs=self.crs,
                    schema={"geometry": self.geometry, "properties": properties},
                ):
                    return  # no feature to save, only the schema is saved

            # Keep only selected fields
            self.gdf = self.gdf.drop(
                columns=[
                    name for name in self.gdf.columns if name not in ["geometry", "fid"] + list(self.fields.keys())
                ]
            )

            # FID is a specific GPKG column id. If already present, it must be an integer.
            if "fid" in self.gdf.columns:
                try:
                    self.gdf["fid"] = self.gdf["fid"].astype("int64")
                except ValueError:
                    self.gdf = self.gdf.drop(columns=["fid"])

            # Export to gpkg using pysewer export function
            write_gdf_to_gpkg(self.gdf, output_path, layer=self.layer_name, crs=self.crs)

    class StationsSpecs(PysewerToGpkgSpecs):
        layer_name = ""
        geometry = "Point"
        fields = {
            "elevation": "float",
            "peak_flow": "float",
            "average_daily_flow": "float",
            "upstream_pe": "int",
            "inflow_trench_depths": "str",
            "total_static_head": "float",
        }

    class PumpingStationsSpecs(StationsSpecs):
        layer_name = "pumping_stations"

    class LiftingStationsSpecs(StationsSpecs):
        layer_name = "lifting_stations"

    class SewerNetworkSpecs(PysewerToGpkgSpecs):
        layer_name = "sewer_pipes"
        geometry = "LineString"
        fields = {
            "distance": "float",
            "profile": "str",
            "needs_pump": "bool",
            "pressurized": "bool",
            "trench_depth_profile": "str",
            "mean_td": "float",
            "diameter": "float",
            "peak_flow": "float",
            "sink_coords": "str",
        }

    class SinksSpecs(PysewerToGpkgSpecs):
        layer_name = "sinks_layer"
        geometry = "Point"
        fields = {
            "elevation": "float",
            "sink_coords": "str",
            "upstream_pe": "int",
            "trench_depth": "float",
            "peak_flow": "float",
            "average_daily_flow": "float",
            "inflow_trench_depths": "str",
            "inflow_diameters": "str",
            "TSS_in": "float",
            "BOD5_in": "float",
            "TKN_in": "float",
            "COD_in": "float",
            "NO3N_in": "float",
            "TP_in": "float",
            "ecoli_in": "float",
            "TSS_obj": "float",
            "BOD5_obj": "float",
            "TKN_obj": "float",
            "COD_obj": "float",
            "NO3N_obj": "float",
            "TN_obj": "float",
            "TP_obj": "float",
            "ecoli_obj": "float",
        }

        def __init__(self, gdf: gpd.GeoDataFrame, crs: CRS):
            super().__init__(gdf, crs)

            # Add columns for input concentrations
            self.gdf["TSS_in"] = float("nan")
            self.gdf["BOD5_in"] = float("nan")
            self.gdf["TKN_in"] = float("nan")
            self.gdf["COD_in"] = float("nan")
            self.gdf["NO3N_in"] = float("nan")
            self.gdf["TP_in"] = float("nan")
            self.gdf["ecoli_in"] = float("nan")

            # Add columns for desired concentrations
            self.gdf["TSS_obj"] = float("nan")
            self.gdf["BOD5_obj"] = float("nan")
            self.gdf["TKN_obj"] = float("nan")
            self.gdf["COD_obj"] = float("nan")
            self.gdf["NO3N_obj"] = float("nan")
            self.gdf["TN_obj"] = float("nan")
            self.gdf["TP_obj"] = float("nan")
            self.gdf["ecoli_obj"] = float("nan")

    custom_config = load_config(filename)
    # Instantiate the model domain
    test_model_domain = ModelDomain(
        dem=custom_config.preprocessing.dem_file_path,
        buildings=custom_config.preprocessing.buildings_input_data,
        roads=custom_config.preprocessing.roads_input_data,
        clustering=custom_config.preprocessing.clustering,
    )

    if sinks_path is not None:
        # If sinks are loaded from a file
        layer = gpd.read_file(sinks_path)
        coordonnees = [(point.x, point.y) for point in layer["geometry"]]
        for geom in coordonnees:
            test_model_domain.add_sink(geom)
    else:
        # Generate sink using pysewer
        test_model_domain.set_sink_lowest()  # put a single sink on the lowest point

    # create the the graph conections ; this is to be used for the routing algorithm
    connection_graph = test_model_domain.generate_connection_graph()

    layout = rsph_tree(connection_graph, test_model_domain.get_sinks(), "building")

    g = estimate_peakflow(
        layout,
        inhabitants_dwelling_attribute_name=custom_config.optimization.inhabitants_dwelling_attribute_name,
        default_inhabitants_dwelling=custom_config.optimization.default_inhabitants_dwelling,
        daily_wastewater_person=custom_config.optimization.daily_wastewater_person,
    )
    g = calculate_hydraulic_parameters(
        layout,
        sinks=test_model_domain.get_sinks(),
        diameters=custom_config.optimization.diameters,
        pressurized_diameter=custom_config.optimization.pressurized_diameter,
        include_private_sewer=True,
        roughness=custom_config.optimization.roughness,
    )

    # Export all the gdf (GeoDataFrame) to GPKG
    export_crs = test_model_domain.dem.get_crs
    for spec in [
        LiftingStationsSpecs(get_node_gdf(g, field="lifting_station", value=True), export_crs),
        PumpingStationsSpecs(get_node_gdf(g, field="pumping_station", value=True), export_crs),
        SinksSpecs(
            get_node_gdf(
                g, field=custom_config.preprocessing.field_get_sinks, value=custom_config.preprocessing.value_get_sinks
            ),
            export_crs,
        ),
        SewerNetworkSpecs(get_edge_gdf(g, detailed=True), export_crs),
    ]:
        cast(PysewerToGpkgSpecs, spec).write_to_gpkg(str(output_path))

    # Create and fill info_network layer
    conn = sqlite3.connect(str(output_path))
    info_network = get_sewer_info(g)
    info_network["Pumping Stations"] = info_network["Pumping Stations"] + info_network["Private Pumps"]
    del info_network["Private Pumps"]
    info_network = {k: [v] for k, v in info_network.items()}

    df = pd.DataFrame.from_dict(info_network)
    df["datetime"] = [pd.to_datetime("today").strftime("%Y-%m-%d %H:%M:%S")]
    try:
        df.to_sql(name="info_network", con=conn, if_exists="fail")
        conn.execute(
            "insert into gpkg_contents (table_name, data_type, identifier) "
            "values ('info_network', 'attributes', 'info_network')"
        )
    except ValueError:
        df.to_sql(name="info_network", con=conn, if_exists="replace")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
