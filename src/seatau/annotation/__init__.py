"""Annotation pipeline: translated artefact <-> reviewer workbook <-> {lang}/.

See seatau/annotation/README.md for the full workflow.
"""

from seatau.annotation.import_reviewed import import_reviewed

__all__ = ["import_reviewed"]
