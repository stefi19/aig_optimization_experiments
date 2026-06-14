# HTML Research Presentation

This folder contains an offline HTML slide deck for the project:

```text
Exact and Approximate Internal Correspondence Recovery After Logic Synthesis Optimization
```

## How to open

Open `docs/presentation/index.html` in a browser.

From the repository root on macOS:

```bash
open docs/presentation/index.html
```

No internet connection or external CDN is required. The deck uses local
HTML/CSS/JavaScript and local copies of the selected plot images under
`docs/presentation/assets/plots/`, so opening `index.html` directly should show
the figures.

## Controls

- `ArrowRight` or `Space`: next slide
- `ArrowLeft`: previous slide
- `Home`: first slide
- `End`: last slide
- `N` or the `Notes` button: toggle speaker notes

## How to present this

Use the first slides to motivate the problem with the compiler analogy, then
slow down through the beginner theory section: digital circuits, gates, internal
nodes, RTL, BLIF, ABC, truth tables, support, signatures, SAT/CEC, and the match
types. The small `a`, `b`, `c` circuit is used as a running example.

The middle slides are the research results. Emphasize the story change from small
benchmarks to ISCAS-85: non-exact recovery exists, but heuristics are noisy and
need SAT validation. Then explain approximate distance as a bridge from "not
equivalent" to "still close", and end with the critical-path prototype as the
first end-to-end use case.

Use the limitations slide to be precise: the current critical path is structural,
sampled approximate distance is not formal, and RTL/timing/register insertion
are future work.
