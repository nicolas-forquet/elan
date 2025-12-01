"""
This module is used for funtions that need QGIS
"""

import sys
from pathlib import Path


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
