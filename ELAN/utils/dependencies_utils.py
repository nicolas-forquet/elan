# pylint:disable=global-statement

"""
Utils functions for managing pysewer install and its dependencies
"""

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

PYSEWER_COMMIT_HASH = "22eb40dc3a921a5cbdd0329b70c9f9aba53631a4"
WETLANDOPTIMIZER_COMMIT_HASH = "b8a6225bfe9f483b619b703097c03e195cd59fdd"


def downloadEnded():
    """Set global download ended flag"""
    global DOWNLOAD_ENDED
    DOWNLOAD_ENDED = True


def downloadError(err_msg):
    """Set global download error message"""

    global DOWNLOAD_ERROR_MSG
    DOWNLOAD_ERROR_MSG = err_msg


def pysewerInstalled(external_deps=False):
    """
    Returns True if pysewer is installed.
    If external_deps is True, add external_dependencies folder to search path.
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
    if external_deps:
        kwargs["args"] += ["--external-deps", DIR_PLUGIN_ROOT / "external_dependencies"]

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


def installPysewer():  # pylint:disable=too-many-statements,too-many-locals
    """Install pysewer in external_dependencies directory"""

    global DOWNLOAD_ENDED
    DOWNLOAD_ENDED = False
    global DOWNLOAD_ERROR_MSG
    DOWNLOAD_ERROR_MSG = ""

    external_dependencies_dir = DIR_PLUGIN_ROOT / "external_dependencies"
    external_dependencies_dir.mkdir(exist_ok=True)

    if (qgsApplication := QgsApplication.instance()) is None:
        raise RuntimeError("QgsApplication not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        zipfile = str(Path(temp_dir) / "pysewer.zip")

        downloader = QgsFileDownloader(
            QUrl(
                f"https://git.ufz.de/despot/pysewer/-/archive/{PYSEWER_COMMIT_HASH}/pysewer-{PYSEWER_COMMIT_HASH}.zip"
            ),
            zipfile,
        )
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
                raise RuntimeError(f"Download timeout (timeout is set to {timeout} seconds)")
            raise RuntimeError(f"Download error ({DOWNLOAD_ERROR_MSG}), check your internet connection")

        if not Path(zipfile).exists():
            raise RuntimeError("Can't download pysewer, check your internet connection")

        res, _ = QgsZipUtils.unzip(zipfile, temp_dir)  # type: ignore
        if not res:
            raise RuntimeError("Unzip error")

        interpreter_path = getInterpreterPath()
        install_deps_kwargs = {
            "args": [
                interpreter_path,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "-r",
                DIR_PLUGIN_ROOT / "resources" / "pysewer" / "pysewer_requirements.txt",
                "-t",
                external_dependencies_dir,
            ]
        }
        install_pysewer_kwargs = {
            "args": [
                interpreter_path,
                "-m",
                "pip",
                "install",
                "--no-deps",
                Path(temp_dir) / f"pysewer-{PYSEWER_COMMIT_HASH}",
                "-t",
                external_dependencies_dir,
            ]
        }
        default_run_options = {
            "check": True,
            "capture_output": True,
            "text": True,
        }
        if sys.platform.startswith("win"):
            si = subprocess.STARTUPINFO()  # type: ignore
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
            default_run_options["startupinfo"] = si
        install_deps_kwargs.update(default_run_options)  # type: ignore
        install_pysewer_kwargs.update(default_run_options)  # type: ignore

        try:
            # Install pysewer dependencies
            res = subprocess.run(**install_deps_kwargs)  # type: ignore

            # Patch pysewer (we don't handle deleted/moved/added files, but only modifications)
            if str(external_dependencies_dir) not in sys.path:
                site.addsitedir(str(external_dependencies_dir))
            import whatthepatch  # type: ignore import outside top level

            for diff in whatthepatch.parse_patch(
                (DIR_PLUGIN_ROOT / "resources" / "pysewer" / "pysewer.patch").read_text()
            ):
                if (header := diff.header) is None:
                    raise RuntimeError("Error while applying patch")
                original_file = Path(temp_dir) / f"pysewer-{PYSEWER_COMMIT_HASH}" / header.old_path
                patched_text = whatthepatch.apply_diff(diff, original_file.read_text())
                original_file.write_text("\n".join(patched_text))

            # Install pysewer
            res = subprocess.run(**install_pysewer_kwargs)  # type: ignore

        except subprocess.CalledProcessError as e:
            shutil.rmtree(external_dependencies_dir)
            raise RuntimeError(f"Command {e.cmd} failed\nOutput: {e.stdout}\nError: {e.stderr}") from e
        except Exception as e:
            shutil.rmtree(external_dependencies_dir)
            raise RuntimeError(f"Unknown error: {e}") from e


def wetlandoptimizerInstalled():
    """
    Returns True if wetlandoptimizer is installed.
    """

    return importutil.find_spec("wetlandoptimizer") is not None


def installWetlandoptimizer():  # pylint:disable=too-many-statements,too-many-locals
    """Install wetlandoptimizer in external_dependencies directory"""

    global DOWNLOAD_ENDED
    DOWNLOAD_ENDED = False
    global DOWNLOAD_ERROR_MSG
    DOWNLOAD_ERROR_MSG = ""

    external_dependencies_dir = DIR_PLUGIN_ROOT / "external_dependencies"
    external_dependencies_dir.mkdir(exist_ok=True)

    if (qgsApplication := QgsApplication.instance()) is None:
        raise RuntimeError("QgsApplication not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        zipfile = str(Path(temp_dir) / "wetlandoptimizer.zip")

        downloader = QgsFileDownloader(
            QUrl(
                # f"https://forgemia.inra.fr/reversaal/nature-based-solutions/caribsan/wetlandoptimizer/-/archive/{WETLANDOPTIMIZER_COMMIT_HASH}/wetlandoptimizer-{WETLANDOPTIMIZER_COMMIT_HASH}.zip"
                f"https://github.com/Djedouas/wetlandoptimizer/archive/{WETLANDOPTIMIZER_COMMIT_HASH}.zip"
            ),
            zipfile,
        )
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
                raise RuntimeError(f"Download timeout (timeout is set to {timeout} seconds)")
            raise RuntimeError(f"Download error ({DOWNLOAD_ERROR_MSG}), check your internet connection")

        if not Path(zipfile).exists():
            raise RuntimeError("Can't download wetlandoptimizer, check your internet connection")

        res, _ = QgsZipUtils.unzip(zipfile, temp_dir)  # type: ignore
        if not res:
            raise RuntimeError("Unzip error")

        interpreter_path = getInterpreterPath()
        install_deps_kwargs = {
            "args": [
                interpreter_path,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "-r",
                DIR_PLUGIN_ROOT / "resources" / "wetlandoptimizer" / "wetlandoptimizer_requirements.txt",
                "-t",
                external_dependencies_dir,
            ]
        }
        install_wetlandoptimizer_kwargs = {
            "args": [
                interpreter_path,
                "-m",
                "pip",
                "install",
                "--no-deps",
                Path(temp_dir) / f"wetlandoptimizer-{WETLANDOPTIMIZER_COMMIT_HASH}",
                "-t",
                external_dependencies_dir,
            ]
        }
        default_run_options = {
            "check": True,
            "capture_output": True,
            "text": True,
        }
        if sys.platform.startswith("win"):
            si = subprocess.STARTUPINFO()  # type: ignore
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore
            default_run_options["startupinfo"] = si
        install_deps_kwargs.update(default_run_options)  # type: ignore
        install_wetlandoptimizer_kwargs.update(default_run_options)  # type: ignore

        try:
            # install wetlandoptimizer dependencies
            res = subprocess.run(**install_deps_kwargs)  # type: ignore

            # Patch pysewer (we don't handle deleted/moved/added files, but only modifications)
            if str(external_dependencies_dir) not in sys.path:
                site.addsitedir(str(external_dependencies_dir))
            import whatthepatch  # type: ignore

            for diff in whatthepatch.parse_patch(
                (DIR_PLUGIN_ROOT / "resources" / "wetlandoptimizer" / "wetlandoptimizer.patch").read_text()
            ):
                if (header := diff.header) is None:
                    raise RuntimeError("Error while applying patch")
                original_file = Path(temp_dir) / f"wetlandoptimizer-{WETLANDOPTIMIZER_COMMIT_HASH}" / header.old_path
                try:
                    patched_text = whatthepatch.apply_diff(diff, original_file.read_text())
                except FileNotFoundError:
                    raise FileNotFoundError("File to patch {} is not in the downloaded files".format(original_file))
                original_file.write_text("\n".join(patched_text))

            # Install wetlandoptimizer
            res = subprocess.run(**install_wetlandoptimizer_kwargs)  # type: ignore

        except subprocess.CalledProcessError as e:
            shutil.rmtree(external_dependencies_dir)
            raise RuntimeError(f"Command {e.cmd} failed\nOutput: {e.stdout}\nError: {e.stderr}") from e
        except Exception as e:
            shutil.rmtree(external_dependencies_dir)
            raise RuntimeError(f"Unknown error: {e}") from e


def removeDependencies():
    external_dependencies_dir = DIR_PLUGIN_ROOT / "external_dependencies"
    if external_dependencies_dir.exists():
        shutil.rmtree(external_dependencies_dir)
