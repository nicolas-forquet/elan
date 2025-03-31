import psycopg2


def create_alti_base_graph(
    conn_str: str,
    #  buildings_schema: str,
    #  buildings_table: str,
    #  zone_schema: str,
    #  zone_table: str,
):
    with psycopg2.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute("select graph.creer_graph_mnt()")


def create_road_base_graph(
    conn_str: str,
    #  roads_schema: str,
    #  roads_table: str,
    #  buildings_schema: str,
    #  buildings_table: str,
    #  zone_schema: str,
    #  zone_table: str,
):
    with psycopg2.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute("select graph.creer_graph_route()")
