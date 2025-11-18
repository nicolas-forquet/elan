# pylint:disable=global-statement

"""
Utils functions for managing pysewer and wetlandoptimizer install and its dependencies
"""

import argparse
import shutil
import site
import subprocess
import sys
import tempfile
import time
from importlib import util as importutil
from pathlib import Path

from qgis.core import QgsApplication, QgsFileDownloader, QgsZipUtils
from qgis.PyQt.QtCore import QUrl

from ELAN.__about__ import DIR_PLUGIN_ROOT
from ELAN.utils.qgis_utils import getInterpreterPath

DOWNLOAD_ENDED = False
DOWNLOAD_ERROR_MSG = ""

EXTERNAL_LIRBARIES_DIR = DIR_PLUGIN_ROOT / "external_libraries"

WETLANDOPTIMIZER_COMMIT_HASH = "cbb4ad058c2bae04fdb0cbc8f98c1f2cf84125be"
PYSEWER_COMMIT_HASH = "c6cd52c8ba1c00f9ebcb91cc75bec50d8a4f72e2"


def downloadEnded():
    """Set global download ended flag"""
    global DOWNLOAD_ENDED
    DOWNLOAD_ENDED = True


def downloadError(err_msg):
    """Set global download error message"""
    global DOWNLOAD_ERROR_MSG
    DOWNLOAD_ERROR_MSG = err_msg


def installPysewer():
    """
    Install pysewer in EXTERNAL_LIRBARIES_DIR
    """

    installLibrary(
        "pysewer",
        f"https://github.com/Djedouas/pysewer/archive/{PYSEWER_COMMIT_HASH}.zip",
    )


def installWetlandoptimizer():
    """
    Install wetlandoptimizer in EXTERNAL_LIRBARIES_DIR
    """

    installLibrary(
        "wetlandoptimizer",
        f"https://github.com/Djedouas/wetlandoptimizer/archive/{WETLANDOPTIMIZER_COMMIT_HASH}.zip",
    )


def pysewerInstalled(external_libs=False):
    """
    Returns True if pysewer is installed.
    If external_libs is True, add EXTERNAL_LIRBARIES_DIR folder to search path.
    """

    kwargs = {
        "args": [
            getInterpreterPath(),
            DIR_PLUGIN_ROOT / "resources" / "pysewer" / "pysewer_launcher.py",
            "--check-installed",
        ],
        "check": True,
        "capture_output": True,
        "text": True,
    }
    if external_libs:
        kwargs["args"] += ["--external-libs", EXTERNAL_LIRBARIES_DIR]

    if sys.platform.startswith("win"):
        si = subprocess.STARTUPINFO()  # type: ignore
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
        kwargs["startupinfo"] = si

    try:
        res = subprocess.run(**kwargs)  # pylint:disable=subprocess-run-check
    except (TypeError, FileNotFoundError) as e:
        raise RuntimeError("No python interpreter found") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr) from e

    return res.stdout.strip() != "pysewer is not installed"


def installLibrary(library_name: str, library_url: str):  # pylint:disable=too-many-statements,too-many-locals
    """Install library in external_dependencies directory"""

    global DOWNLOAD_ENDED
    global DOWNLOAD_ERROR_MSG
    DOWNLOAD_ENDED = False
    DOWNLOAD_ERROR_MSG = ""

    EXTERNAL_LIRBARIES_DIR.mkdir(exist_ok=True)

    if (qgsApplication := QgsApplication.instance()) is None:
        raise RuntimeError("QgsApplication not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        zipfile = str(Path(temp_dir) / f"{library_name}.zip")
        downloader = QgsFileDownloader(QUrl(library_url), zipfile)
        downloader.downloadCanceled.connect(lambda: downloadError("canceled"))
        downloader.downloadError.connect(downloadError)
        downloader.downloadExited.connect(lambda: downloadError("exited"))
        downloader.downloadCompleted.connect(downloadEnded)
        downloader.startDownload()
        timeout = 60  # secs
        start_time = time.time()
        while not DOWNLOAD_ERROR_MSG and not DOWNLOAD_ENDED and not time.time() - start_time > timeout:
            time.sleep(1)
            qgsApplication.processEvents()
        if not DOWNLOAD_ENDED:
            if time.time() - start_time > timeout:
                raise RuntimeError(f"Download timeout! (timeout is set to {timeout} seconds)")
            raise RuntimeError(f"Download error ({DOWNLOAD_ERROR_MSG}), check your internet connection")

        if not Path(zipfile).exists():
            raise RuntimeError(f"Can't download {library_name}, check your internet connection")

        res, _ = QgsZipUtils.unzip(zipfile, temp_dir)  # type: ignore
        if not res:
            raise RuntimeError("Unzip error")

        interpreter_path = getInterpreterPath()
        cmd_args = [
            interpreter_path,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "-t",
            EXTERNAL_LIRBARIES_DIR,
        ]
        run_options = {
            "check": True,
            "capture_output": True,
            "text": True,
        }
        if sys.platform.startswith("win"):
            si = subprocess.STARTUPINFO()  # type: ignore
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
            run_options["startupinfo"] = si

        try:
            # Install dependencies
            run_options["args"] = cmd_args + [
                "-r",
                DIR_PLUGIN_ROOT / "resources" / library_name / f"{library_name}_requirements.txt",
            ]
            res = subprocess.run(**run_options)  # type: ignore

            # Install library: get first directory in the
            run_options["args"] = cmd_args + [next(Path(temp_dir).iterdir())]
            res = subprocess.run(**run_options)  # type: ignore

        except subprocess.CalledProcessError as e:
            removeDependencies()
            raise RuntimeError(f"Command {e.cmd} failed\nOutput: {e.stdout}\nError: {e.stderr}") from e
        except Exception as e:
            removeDependencies()
            raise RuntimeError(f"Unknown error: {e}") from e


def wetlandoptimizerInstalled():
    """
    Returns True if wetlandoptimizer is installed.
    """

    return importutil.find_spec("wetlandoptimizer") is not None


def removeDependencies():
    if EXTERNAL_LIRBARIES_DIR.exists():
        shutil.rmtree(EXTERNAL_LIRBARIES_DIR)

    # "unload" modules
    if "wetlandoptimizer" in sys.modules:
        sys.modules.pop("wetlandoptimizer")


if __name__ == "__main__":
    """
    If this file is exectuted, this is a CLI to install ELAN dependencies.
    Useful in CI/CD to be called before executing tests.
    """

    parser = argparse.ArgumentParser(description="install libraries")
    parser.add_argument(
        "--install-pysewer",
        help=f"install pysewer and its dependencies in {EXTERNAL_LIRBARIES_DIR} directory",
        action="store_true",
    )
    parser.add_argument(
        "--install-wetlandoptimizer",
        help=f"install wetlandoptimizer and its dependencies in {EXTERNAL_LIRBARIES_DIR} directory",
        action="store_true",
    )
    parser.add_argument(
        "--install-all",
        help=f"install all libraries and their dependencies in {EXTERNAL_LIRBARIES_DIR} directory",
        action="store_true",
    )
    parser.add_argument(
        "--delete-libraries",
        help=f"delete external libraries directory {EXTERNAL_LIRBARIES_DIR}",
        action="store_true",
    )
    args = parser.parse_args()

    if not any(
        [
            args.install_pysewer,
            args.install_wetlandoptimizer,
            args.install_all,
            args.delete_libraries,
        ]
    ):
        parser.print_help()
        sys.exit(0)

    app = QgsApplication([], False)
    app.initQgis()

    if args.delete_libraries:
        removeDependencies()

    if EXTERNAL_LIRBARIES_DIR.exists():
        raise RuntimeError(f"{EXTERNAL_LIRBARIES_DIR} already exists, not overwriting")

    if args.install_pysewer or args.install_all:
        installPysewer()
        print(f"pysewer and its dependencies are now installed in {EXTERNAL_LIRBARIES_DIR} directory")

    if args.install_wetlandoptimizer or args.install_all:
        installWetlandoptimizer()
        print(f"wetlandoptimizer and its dependencies are now installed in {EXTERNAL_LIRBARIES_DIR} directory")
