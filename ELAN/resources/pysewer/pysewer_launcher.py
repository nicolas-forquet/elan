"""
Script to launch pysewer computation
"""

import argparse
import importlib.util
import pathlib
import site
import sqlite3
from pathlib import Path
from typing import Optional


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
        else:
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
    import geopandas as gpd
    import pandas as pd
    from pysewer import ModelDomain
    from pysewer.config.settings import load_config
    from pysewer.export import write_gdf_to_gpkg
    from pysewer.helper import get_edge_gdf, get_node_gdf, get_sewer_info
    from pysewer.optimization import calculate_hydraulic_parameters, estimate_peakflow
    from pysewer.routing import rsph_tree

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
    sewer_network_gdf = get_edge_gdf(g, detailed=True)
    pumping_network_gdf = get_node_gdf(g, field="pumping_station", value=True)
    lifting_network_gdf = get_node_gdf(g, field="lifting_station", value=True)
    sinks_gdf = get_node_gdf(
        g, field=custom_config.preprocessing.field_get_sinks, value=custom_config.preprocessing.value_get_sinks
    )

    # Keep only specific columns
    sewer_network_gdf = sewer_network_gdf.drop(
        columns=[
            name
            for name in sewer_network_gdf.columns
            if name
            not in [
                "fid",
                "distance",
                "profile",
                "needs_pump",
                "pressurized",
                "trench_depth_profile",
                "mean_td",
                "diameter",
                "peak_flow",
                "sink_coords",
                "geometry",
            ]
        ]
    )
    stations_columns_to_keep = [
        "fid",
        "elevation",
        "peak_flow",
        "average_daily_flow",
        "upstream_pe",
        "inflow_trench_depths",
        "total_static_head",
        "geometry",
    ]
    pumping_network_gdf = pumping_network_gdf.drop(
        columns=[name for name in pumping_network_gdf.columns if name not in stations_columns_to_keep]
    )
    lifting_network_gdf = lifting_network_gdf.drop(
        columns=[name for name in lifting_network_gdf.columns if name not in stations_columns_to_keep]
    )
    sinks_gdf = sinks_gdf.drop(
        columns=[
            name
            for name in sinks_gdf.columns
            if name
            not in [
                "fid",
                "elevation",
                "sink_coords",
                "upstream_pe",
                "trench_depth",
                "peak_flow",
                "average_daily_flow",
                "inflow_trench_depths",
                "inflow_diameters",
                "geometry",
            ]
        ]
    )

    # Add columns for desired concentrations
    sinks_gdf["TSS_obj"] = float("nan")
    sinks_gdf["BOD5_obj"] = float("nan")
    sinks_gdf["TKN_obj"] = float("nan")
    sinks_gdf["COD_obj"] = float("nan")
    sinks_gdf["NO3_obj"] = float("nan")
    sinks_gdf["TN_obj"] = float("nan")
    sinks_gdf["P_obj"] = float("nan")
    sinks_gdf["col_obj"] = float("nan")

    # Export all the gdf (GeoDataFrame) to GPKG
    export_crs = test_model_domain.dem.get_crs
    for gdf, layer_name in [
        (lifting_network_gdf, "lifting_stations"),
        (pumping_network_gdf, "pumping_stations"),
        (sinks_gdf, "sinks_layer"),
        (sewer_network_gdf, "sewer_pipes"),
    ]:
        # FID is a specific GPKG column id. If already present, it must be an integer.
        if "fid" in gdf.columns:
            try:
                gdf["fid"] = gdf["fid"].astype("int64")
            except ValueError:
                gdf = gdf.drop(columns=["fid"])

        write_gdf_to_gpkg(gdf, str(output_path), layer=layer_name, crs=export_crs)

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
