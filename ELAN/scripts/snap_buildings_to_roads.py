from collections import defaultdict

import geopandas as gpd
from shapely.geometry import LineString, Point


def explode_multilines(gdf):
    """
    Explodes MultiLineStrings into individual LineStrings.
    """
    gdf = gdf.explode(ignore_index=True)
    return gdf[gdf.geometry.type == "LineString"].reset_index(drop=True)


def snap_buildings_to_road_vertices(buildings_gdf, roads_gdf, value_field, max_distance=500):
    """
    Snap centroids to road vertices, aggregate population at each vertex,
    and return individual building status and projection lines.

    Returns:
        - aggregated_gdf: snapped vertex points with sum + count
        - projection_lines_gdf: LineStrings from original centroid to snapped vertex
    """

    if buildings_gdf.crs != roads_gdf.crs:
        raise ValueError("CRS mismatch between buildings and roads")

    roads_gdf = explode_multilines(roads_gdf)
    roads_gdf = roads_gdf[roads_gdf.geometry.is_valid]
    buildings_gdf = buildings_gdf.copy()
    buildings_gdf["area"] = buildings_gdf.geometry.area

    total_area = buildings_gdf["area"].sum()
    buildings_gdf["population"] = buildings_gdf["area"] / total_area * value_field
    value_field = "population"

    # Extract all road vertices
    vertex_index = {}
    vertices = []
    for line in roads_gdf.geometry:
        for coord in line.coords:
            pt = Point(coord)
            key = (round(pt.x, 6), round(pt.y, 6))
            if key not in vertex_index:
                vertex_index[key] = pt
                vertices.append(pt)

    vertex_gdf = gpd.GeoDataFrame(geometry=vertices, crs=roads_gdf.crs)
    vertex_sindex = vertex_gdf.sindex

    # Containers
    aggregation = defaultdict(lambda: {"geometry": None, "count": 0, str(value_field): 0.0})
    projection_lines = []
    building_records = []

    for _, row in buildings_gdf.iterrows():
        centroid = row.geometry.centroid
        value = row[value_field]

        # Find nearest vertex within threshold
        possible_idx = list(vertex_sindex.intersection(centroid.buffer(max_distance).bounds))
        candidates = vertex_gdf.iloc[possible_idx]

        nearest_pt = None
        min_dist = float("inf")
        for _, v_row in candidates.iterrows():
            dist = centroid.distance(v_row.geometry)
            if dist < min_dist and dist <= max_distance:
                nearest_pt = v_row.geometry
                min_dist = dist

        if nearest_pt:
            # Snap and aggregate
            key = (round(nearest_pt.x, 6), round(nearest_pt.y, 6))
            pt = vertex_index[key]
            aggregation[key]["geometry"] = pt
            aggregation[key]["count"] += 1
            aggregation[key][str(value_field)] += value

            # Record projection line
            projection_lines.append(LineString([(centroid.x, centroid.y), (pt.x, pt.y)]))

            # Record individual building
            building_records.append({**row.drop("geometry"), "geometry": pt, "status": "snapped"})

        else:
            # Not snapped
            building_records.append({**row.drop("geometry"), "geometry": centroid, "status": "not_snapped"})

    # Build outputs
    aggregated_gdf = gpd.GeoDataFrame(list(aggregation.values()), crs=buildings_gdf.crs)
    lines_gdf = gpd.GeoDataFrame(geometry=projection_lines, crs=buildings_gdf.crs)

    return aggregated_gdf, lines_gdf
