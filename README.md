# TCG Card Recognizer

An importable Python package that matches trading card images against a bundled
SQLite database using perceptual hashes. Requires Python 3.14 or newer.

## Installation

From another Python project, install this repository:

```sh
pip install /path/to/tcg-card-recognizer
```

For an editable local dependency:

```sh
pip install -e /path/to/tcg-card-recognizer
```

With uv, run `uv add /path/to/tcg-card-recognizer` in the consuming project.
The database is included in both the wheel and source distribution; no separate
download or database setup is required.

## Usage

```python
from pathlib import Path

from tcg_card_recognizer import Recognizer

recognizer = Recognizer()
matches = recognizer.recognize(Path("card.png").read_bytes(), top_k=5)

for distance, card_id, name, number, set_abbreviation in matches:
    print(f"{name} - {number}, {set_abbreviation}, distance={distance}")
```

Matches are returned as tuples in ascending hash-distance order (lower is closer).
Recognition does not print results. Images must contain a cropped card; this
package does not detect card boundaries in photographs.

To use your own database with the same schema:

```python
recognizer = Recognizer(db_path="/path/to/custom.db")
```

Database connections are read-only and closed after each query. The default
database is resolved relative to the installed package, not the working directory.

## Repository Layout

```text
src/tcg_card_recognizer/
    __init__.py       # Public Recognizer import
    recognizer.py     # Image matching
    tcg-data.db       # Bundled card data
card-hashing/         # Maintainer scripts for populating the database
tests/               # Package and recognition tests
```

## Development

```sh
uv sync --extra data
uv run python -m unittest discover -s tests
uv build
```

The optional `data` dependencies are only needed for the scripts in
`card-hashing/`. These scripts update the database under `src/tcg_card_recognizer/`;
rebuild the package to distribute updated data. Keep notification credentials in
`card-hashing/.env`, which is not included in the package.
