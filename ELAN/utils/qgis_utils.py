"""
This module is used for funtions that need QGIS
"""

import sys
from pathlib import Path
from typing import List, Optional


def getInterpreterPath():
    """
    Returns QGIS specific environment python interpreter.

    Supports Linux and Windows
    """

    interpreter_path = None
    if sys.platform.startswith("win"):
        paths_to_test = [
            Path(sys.executable).parent / file_name for file_name in ["python-qgis-ltr.bat", "python-qgis.bat"]
        ]
        for path_to_test in paths_to_test:
            if path_to_test.exists():
                interpreter_path = path_to_test
                break
    else:
        interpreter_path = Path(sys.executable)

    return interpreter_path


def get_common_connection_string(layers: List) -> Optional[str]:
    """get_common_connection_string.

    Get the connection string from the layers, to create a psycopg2 connection.
    The layers must share the same connection:
      - same service
      or
      - same host, port, database, user, password

    Parameters
    ----------
    layers : List of QgsMapLayer
        layers that must share the same connection

    Returns
    -------
    Optional[str] : None if layers don't share the same connection

    """

    pg_service = set()
    pg_host = set()
    pg_port = set()
    pg_database = set()
    pg_user = set()
    pg_password = set()
    for layer in layers:
        pg_service.add(layer.dataProvider().uri().service() if layer.dataProvider().uri().service() != "" else "None")
        pg_host.add(layer.dataProvider().uri().host() if layer.dataProvider().uri().host() != "" else "None")
        pg_port.add(layer.dataProvider().uri().port() if layer.dataProvider().uri().port() != "" else "None")
        pg_database.add(
            layer.dataProvider().uri().database() if layer.dataProvider().uri().database() != "" else "None"
        )
        pg_user.add(layer.dataProvider().uri().username() if layer.dataProvider().uri().username() != "" else "None")
        pg_password.add(
            layer.dataProvider().uri().password() if layer.dataProvider().uri().password() != "" else "None"
        )
    if all([len(a) == 1 and "None" not in a for a in [pg_host, pg_port, pg_database, pg_user, pg_password]]):
        return (
            f"database={pg_database.pop()} host={pg_host.pop()} "
            f"port={pg_port.pop()} user={pg_user.pop()} password={pg_password.pop()}"
        )
    if len(pg_service) == 1 and "None" not in pg_service:
        return f"service={pg_service.pop()}"
    return None
