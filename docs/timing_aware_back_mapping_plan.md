# Timing-Aware Critical-Path Back-Mapping Plan

## Why Structural Longest Path Is Only A Proxy

The current critical-path prototype walks the deepest chain of internal BLIF nodes. This
is useful for a first mapping experiment because it is deterministic and does not require
a technology library. However, structural depth is not the same as circuit timing.

A path with many simple gates can be faster than a shorter path containing slower mapped
cells. Conversely, a path with fewer logic levels can still dominate timing if one node
maps to a high-delay cell or a large LUT-like function.

## What A Real Timing Path Means

A real timing path is the path with the worst arrival time under a delay model. In a
technology-mapped flow, that delay model comes from a library: each cell has delay
information, often depending on load, slew, pin, and transition direction.

For this project, the ideal engineering flow is:

```text
optimized mapped circuit
  -> timing analysis
  -> critical path with arrival delays
  -> back-map path nodes to original circuit/RTL locations
```

That is more useful than structural depth because it points to the logic that actually
limits clock frequency.

## Why Gate And Library Delays Matter

BLIF `.names` nodes are abstract Boolean functions. Without a library, they do not say
whether a function will become one fast cell, several gates, a large LUT, or part of a
mapped macro. A timing-aware back-mapper eventually needs one of:

- a technology-mapped network with library cell names,
- ABC timing reports after `map` / library loading,
- a conservative proxy delay model when no real library is available.

## ABC Timing Direction

ABC has commands for statistics, mapping, fanin/fanout summaries, and some timing-related
queries depending on the build and loaded libraries. This iteration probes the local ABC
binary for commands such as `ps`, `print_stats`, `print_level`, `print_fanio`, `map`,
`read_library`, `read_lib`, `print_delay`, `stime`, and `topo`.

If a real timing report is available, it could become the source of critical-path nodes.
If not, the project can still make progress with a delay-weighted proxy.

## Current Increment

This iteration adds a lightweight delay model:

- constants: delay `0`,
- buffers / inverters: delay `1`,
- simple 2-input logic: delay `1`,
- larger `.names` nodes: delay `1 + 0.2 * max(0, fanin - 2)` by default.

The script compares the existing structural longest path with a delay-weighted longest
path and maps both using the same correspondence layers. This tells us whether the proxy
selects the same nodes and whether mapping quality changes.

## Future Work

This is not real physical timing yet. Remaining work includes:

- loading a real technology library,
- extracting ABC timing paths after technology mapping,
- preserving path-node provenance through mapping,
- connecting timing-path nodes to RTL/source locations,
- using verified timing paths to drive register-insertion suggestions.
