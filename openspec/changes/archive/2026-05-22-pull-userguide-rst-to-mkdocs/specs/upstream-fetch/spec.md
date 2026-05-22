## ADDED Requirements

### Requirement: Fetch RST source from upstream GitHub
The system SHALL provide a `fetch_upstream.py` script that clones the `doc/userguide/src/` directory from `https://github.com/robotframework/robotframework` using git sparse-checkout and copies the result into the local `doc/userguide/src/` path.

#### Scenario: Successful fetch from default ref
- **WHEN** `fetch_upstream.py` is run without arguments
- **THEN** it clones `master` branch of robotframework/robotframework with `--depth=1 --filter=blob:none --sparse`
- **THEN** only `doc/userguide/src/` is checked out
- **THEN** the contents are copied into the local `doc/userguide/src/` directory, replacing existing files
- **THEN** the temp clone directory is removed
- **THEN** a `.upstream-lock.json` file is written with the fetched commit SHA, ref, and ISO-8601 timestamp

#### Scenario: Successful fetch from specific ref
- **WHEN** `fetch_upstream.py --ref v7.2.1` is run
- **THEN** it clones the `v7.2.1` tag instead of `master`
- **THEN** all other behavior is identical to the default-ref scenario

#### Scenario: git not available
- **WHEN** `fetch_upstream.py` is run and `git` is not on PATH
- **THEN** it prints a clear error: "git is required but not found on PATH"
- **THEN** it exits with a non-zero exit code without modifying any local files

#### Scenario: Upstream directory structure missing expected paths
- **WHEN** the cloned repository does not contain `doc/userguide/src/`
- **THEN** `fetch_upstream.py` prints an error identifying the missing path
- **THEN** it exits with a non-zero exit code without overwriting local files

### Requirement: Record upstream provenance
The system SHALL write a `.upstream-lock.json` file after each successful fetch so that conversion output is traceable to a specific upstream commit.

#### Scenario: Lock file written on success
- **WHEN** a fetch completes successfully
- **THEN** `.upstream-lock.json` is written in `doc/userguide-mkdocs/` containing `ref`, `commit` (full SHA), and `fetched_at` (ISO-8601 UTC)

#### Scenario: Lock file not written on failure
- **WHEN** the fetch fails for any reason
- **THEN** any existing `.upstream-lock.json` is left unmodified
