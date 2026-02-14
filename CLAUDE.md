# The Melting Pod

Static site for a podcast about U.S. immigration policy.

## Build System

```bash
python build.py          # Build all pages
python build.py --clean  # Remove episode-*.html first, then rebuild
```

The build script reads `data/episodes.json` and generates static HTML pages.

## Project Structure

- `build.py` - Main build script with template functions
- `data/episodes.json` - Episode metadata (add new episodes here)
- `styles7.css` / `main7.js` - Site CSS and JS
- `*.html` - Generated pages (don't edit directly)

## Adding Episodes

1. Add entry to `data/episodes.json` with: number, slug, title, date, duration, description
2. Optional fields: megaphone_id (for player embed), image, guest, resources, transcript
3. Run `python build.py`

## Key Patterns

- Templates are inline in `build.py` (no separate template files)
- `{{variable}}` syntax for simple substitution
- Episode slugs become `episode-{slug}.html`
- Images go in project root (not a subdirectory)

## Notes

- The site uses Library of Congress public domain images for historical photos
- Megaphone.fm embeds used for audio players (when megaphone_id is set)
- No package.json - pure Python + vanilla HTML/CSS/JS
