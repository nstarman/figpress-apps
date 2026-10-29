"""figpress-apps: webapps that are the interactive counterparts of scientific papers."""

__version__ = "2026.10.28"

from figpress_apps.build import BuildError, BuildResult, build, inline_modules  # noqa: E402
from figpress_apps.data import DataError, Dataset, export, load  # noqa: E402

__all__ = ["BuildError", "BuildResult", "DataError", "Dataset", "__version__", "build", "export",
           "inline_modules", "load"]
