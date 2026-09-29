# Local station private M3U run kit

This kit is for building a local-station M3U on your own PC.

The repository keeps stream URLs blank. Do not commit filled `stream_url` values.

## Files

- `japan_iptv_local_station_m3u_private_template.csv`
  - Public template.
  - `stream_url` is intentionally blank.
- `local_station_private.csv`
  - Private working copy on your PC.
  - Fill only the `stream_url` column.
  - Ignored by `.gitignore`.
- `local_station_private.m3u`
  - Generated private M3U.
  - Ignored by `.gitignore`.
- `scripts/run_local_station_private_m3u.ps1`
  - Windows helper script.

## First run

Open PowerShell in the repository folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_local_station_private_m3u.ps1 -CreateOnly
```

This creates:

```text
local_station_private.csv
```

Then open `local_station_private.csv` and fill only the `stream_url` column on your PC.

## Build M3U

After filling `stream_url`, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_local_station_private_m3u.ps1
```

Output:

```text
local_station_private.m3u
```

## Current EPG status

Confirmed `tvg-id` values are already in the template for these 8 stations:

- tvk → `テレビ神奈川_jp`
- テレ玉 → `テレ玉_jp`
- TOKYO MX2 → `TOKYO・MX2_jp`
- KBS京都 → `KBS京都_jp`
- サンテレビ → `サンテレビ_jp`
- MBS → `毎日テレビ_jp`
- ABC → `ABCテレビ_jp`
- YTV → `読売テレビ_jp`

Still unresolved:

- チバテレ
- テレビ新広島

## Safety notes

- Do not commit `local_station_private.csv`.
- Do not commit `local_station_private.m3u`.
- Do not add token, vhash, ac_tk, or p2p/p5p entries to public files.
- This repository is metadata-first. Playback URLs stay local only.
