# Repository Guide

## Execution model

- This is a file-based pipeline of standalone scripts, not an installable Python package: `01 scraping/` collects data, `03 analysis/` enriches it, and `02 visual/` renders copied JSON in a static D3 UI.
- Run scripts from their numbered directory. Data inputs and outputs (`followers.txt`, `relations.txt`, and generated files) remain CWD-relative, so root-level invocations can read or write the wrong paths. Config loading is the exception: it is anchored to the repository root and can be overridden with `INSTAGRAM_NETWORK_CONFIG`.
- `03 analysis/helper_functions.py` is shared infrastructure for both analysis and scraping. `01 scraping/insta_utils.py` and `relations_to_json.py` add that directory to `sys.path`; moving or renaming it breaks both stages.
- Preserve `followers_file` handling when changing graph construction. It seeds isolated followers that do not occur in `relations.txt`.

## Commands and ordering

Install from the repository root; dependencies are unpinned and there is no lockfile:

```bash
pip install instaloader -U
pip install -r requirements.txt
```

The authenticated scraping pipeline runs from `01 scraping/`, in this order:

```bash
python3 get_my_followers.py
python3 get_relations.py --wait-time 10
python3 relations_to_json.py
```

- Do not run scraping as validation or without an explicit request. It contacts Instagram, requires an existing Instaloader session, and mutates account-derived data.
- `get_my_followers.py` overwrites `followers.txt` and `followees.txt`. `get_relations.py` appends `relations.txt`, consumes `my_followers_left.txt` as resume state, and may overwrite files under `followers_data/`; use `--max-count N` only when a requested scrape must be bounded.
- `get_relations.py` initializes Instaloader and parses CLI arguments at import time. Do not import it as a library; even `--help` loads the configured session first.
- Omitting `--store-data` prompts for 15 seconds and defaults to enabling it. `external_analysis.py` needs the resulting `01 scraping/followers_data/` files.

Analysis commands run from `03 analysis/` and consume local copies of the generated inputs:

```bash
cp ../01\ scraping/relations.* ../01\ scraping/followers.txt ./
python3 global_analysis.py
python3 local_analysis.py
python3 community_detection.py
python3 advanced_analysis.py
python3 external_analysis.py
```

- Run the copy only when explicitly requested: it overwrites existing `03 analysis/relations.*` and `followers.txt`. Do not run analysis as generic validation; the scripts write JSON and PNG results in place.
- Community detection and the full betweenness/Jaccard work in external analysis can be expensive on large graphs.
- There is no configured test suite, single-test command, lint, formatter, typecheck, CI workflow, build, or task runner. A local `.ruff_cache/` does not define a supported Ruff command.

## Data and visualization

- Treat root `config.json`, relation TXT/JSON files, `01 scraping/followers_data/`, and generated analysis outputs as local account/network data. `.gitignore` contains TXT/JSON patterns, but several matching files and `config.json` are already tracked; never assume such a path is untracked or safe to regenerate.
- Numeric node IDs and JSON ordering from `relations_to_json.py` are not stable because nodes are emitted from a set. For semantic comparisons, map link endpoint IDs back to node names and compare name pairs plus isolated node names, not raw IDs or whole-file ordering.
- `02 visual/index.html` reads `relations.json`; `index_darkmatter.html` reads `relations_darkmatter.json`. The README dark-matter copy example renames the file for the standard page and does not satisfy the dedicated page.
- The visualization has no frontend build step: checked-in HTML/JS loads D3 v4, jQuery, and Lodash from CDNs. Browser checks therefore need network access; the README expects an HTTP server but defines no canonical server command.
