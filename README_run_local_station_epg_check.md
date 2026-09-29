# Run local station EPG check

This repository includes a GitHub Actions workflow for checking whether local-station `tvg-id` candidates exist in an XMLTV EPG file.

## Workflow

```text
.github/workflows/check-local-station-epg.yml
```

## Default EPG source

The manual workflow input defaults to:

```text
https://raw.githubusercontent.com/ajiousama/himitsu/main/guides.xml
```

You can override this with another XMLTV EPG URL when running the workflow manually.

## What it does

1. Downloads the selected XMLTV EPG file as `epg.xml`.
2. Runs:

```bash
python3 scripts/check_local_station_epg_ids.py \
  --epg epg.xml \
  --map japan_iptv_local_station_epg_map.csv \
  --out local_station_epg_check_result.csv
```

3. Prints the result into the workflow summary.
4. Uploads `local_station_epg_check_result.csv` as an artifact.

## Output status

```text
OK      : preferred or alternate tvg-id exists in the EPG XML
MISSING : no candidate ID matched the EPG XML
```

## Safety notes

This workflow checks metadata only.

It does not:

- fetch or test playback URLs
- scrape stream sources
- use token/vhash/ac_tk values
- use p2p/p5p entries
- write private stream URLs

