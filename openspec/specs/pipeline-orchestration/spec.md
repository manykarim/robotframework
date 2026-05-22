## MODIFIED Requirements

### Requirement: Pipeline executes stages in order including fetch
The pipeline (`pipeline.py`) SHALL execute stages in the order: FETCH (Stage 0) → CLEAN → CONVERT → FIX → ASSETS → VALIDATE, where Stage 0 fetches the latest RST source from upstream before any other processing.

#### Scenario: Default run fetches upstream then converts
- **WHEN** `python pipeline.py` is run without flags
- **THEN** Stage 0 (FETCH) runs first, calling `fetch_upstream.py` with the default ref
- **THEN** on successful fetch, the pipeline continues with CLEAN → CONVERT → FIX → ASSETS → VALIDATE
- **THEN** the final site reflects the fetched upstream content

#### Scenario: Skip fetch preserves existing RST
- **WHEN** `python pipeline.py --skip-fetch` is run
- **THEN** Stage 0 is skipped entirely
- **THEN** the pipeline proceeds directly with CLEAN → CONVERT → FIX → ASSETS → VALIDATE using local RST files
- **THEN** behavior is identical to the pre-change pipeline

#### Scenario: Fetch stage failure aborts pipeline
- **WHEN** Stage 0 (FETCH) fails (non-zero exit from `fetch_upstream.py`)
- **THEN** the pipeline prints the fetch error
- **THEN** the pipeline exits without running CLEAN, CONVERT, or any subsequent stages

### Requirement: Pipeline accepts upstream-ref flag
The pipeline SHALL accept an `--upstream-ref` flag that is forwarded to `fetch_upstream.py`.

#### Scenario: Specific ref passed through
- **WHEN** `python pipeline.py --upstream-ref v7.2.1` is run
- **THEN** Stage 0 calls `fetch_upstream.py --ref v7.2.1`
- **THEN** conversion proceeds against the RST content from that ref

#### Scenario: upstream-ref ignored when skip-fetch is set
- **WHEN** `python pipeline.py --skip-fetch --upstream-ref v7.2.1` is run
- **THEN** Stage 0 is skipped; `--upstream-ref` has no effect
