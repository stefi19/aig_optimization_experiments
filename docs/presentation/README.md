# Research presentation

The default `index.html` is the 16-slide formal approximate-correspondence study.
It uses local CSS, JavaScript, figures, and a local publication PDF link.
The original extended presentation is preserved as `legacy.html` with a
supersession notice for historical quantitative distances.

From the repository root:

```bash
make approx-correspondence-pdf
make website
make website-check
make serve-website
```

Visit `http://127.0.0.1:8765/presentation/`.
GitHub Pages uses `main /docs` and the same relative routes under the repository
subpath. `.nojekyll` preserves static filenames. Deploy by pushing the checked
commit to `main`, then inspect the Pages build for that exact commit.

Controls: Prev/Next, ArrowLeft/ArrowRight, Space, PageUp/PageDown, Home/End, N or
Notes, and Overview. Direct links such as `#slide-13` open the selected slide.
All 16 slides were navigated in a browser; images, notes, overview, and hash
navigation were verified. The HTTP checker also traverses the legacy deck.

Generated HTML content comes from
`scripts/publication/build_approximate_website.py`; edit content there and edit
`approximate.css` / `approximate.js` directly. Publication metrics come from
checked CSVs, not hand-entered result estimates.
