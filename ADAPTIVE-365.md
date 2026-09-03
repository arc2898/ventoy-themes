# Adaptive 365-day Ventoy theme collection

This is an additional collection built from the repository’s existing `arc-ventoy-theme.zip` reference. The original files remain unchanged. The collection contains one independently processed theme for each date from **2026-09-03 through 2027-09-02**, arranged in twelve categories.

For every date, the builder obtains a random high-resolution source image at 4096×2354, analyzes candidate menu regions, crops and resizes the image to **1366×786**, chooses the lowest-detail region for the menu, calculates panel transparency from local image complexity, writes the Ventoy `theme.txt`, copies the reference font and menu assets, renders a preview, and includes the result in its category ZIP package.

## Layout behavior

The menu is not fixed to one location. Each day records one of four independently selected regions—`left`, `right`, `left-bottom`, or `right-bottom`—with exact `left`, `top`, `width`, and `height` values in `adaptive-manifest.csv`. The panel uses true alpha assets and a per-image transparency value. The visible header contains the day and ISO date; the menu contains the standard Ventoy item names.

## Contents

| Path | Purpose |
| --- | --- |
| `adaptive-365/` | 365 daily theme folders grouped by category |
| `adaptive-previews/` | 365 actual 1366×786 rendered previews |
| `adaptive-packages/` | 12 category ZIP packages |
| `adaptive-manifest.csv` | Per-day source URL, analysis, geometry, and transparency values |
| `adaptive-manifest.json` | Same metadata in JSON format |
| `build_adaptive_365.py` | Reproducible builder |
| `audit_adaptive_365.py` | Final audit script |
| `adaptive-verification-notes.md` | Notes from inspected real renders |

## Verification limitation

The VM does not contain `qemu-system-x86_64`, `grub-mkrescue`, or `grub-mkstandalone`, so a booted Ventoy/GRUB runtime verification was not possible in this environment. Instead, every day was rendered deterministically at the target resolution from its actual background and computed layout, and all 365 outputs were audited for dimensions, dates, packages, and adaptive regions.

The original reference ZIP and existing repository files were not overwritten.
