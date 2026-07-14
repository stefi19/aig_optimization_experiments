# RTL / Source-Level Back-Mapping Plan

The current correspondence pipeline maps nodes between BLIF-level circuits:

```text
optimized BLIF node -> original BLIF node
```

That is useful for synthesis research, but it is not yet enough for hardware engineers.
Engineers debug and edit RTL source code, not anonymous optimized netlist nodes. A final
critical-path back-mapping tool should explain an optimized path in terms of the original
design source:

```text
optimized critical-path node
  -> original BLIF node
  -> RTL signal / expression / source location
  -> possible register insertion point
```

## What Source-Level Mapping Should Provide

A useful source-level mapping should include:

- RTL signal name, such as `sum_stage` or `carry_next`;
- source file path;
- source line number or line range;
- original expression when it is available;
- module and hierarchy context;
- lowered net or BLIF node name;
- confidence level, because optimization can merge, duplicate, or remove logic.

For register-insertion suggestions, the source metadata should also describe whether the
candidate is combinational logic, sequential logic, part of a control path, or part of a
data path. Suggesting a register at a good Boolean cut is not enough; the transformation
must preserve the design's sequential behavior.

## Why BLIF-Node Mapping Is Not Enough

BLIF node names are often generated names. Even when a BLIF node name resembles an RTL
wire, it may not identify the exact source expression that a designer would edit. After
optimization, a single optimized node may represent logic that came from several RTL
expressions, while one RTL expression may be duplicated into several netlist cones.

This is why the existing correspondence layers are necessary but incomplete. They can say
"optimized node `m57` corresponds to original node `n41`"; they cannot yet say "that node
came from `simple_pipeline.v:12`, expression `mix = a ^ b`."

## How Yosys Can Help

Yosys lowers Verilog/SystemVerilog into intermediate representations, BLIF, JSON, and other
netlist formats. During lowering, it may preserve useful names and attributes, including
source-location attributes such as `src`. In JSON output, this metadata commonly appears on
modules, cells, or netnames.

The first prototype therefore asks a small question:

```text
If we run a tiny Verilog design through Yosys, which signal names and source attributes
survive into JSON or BLIF?
```

If names and `src` attributes survive in JSON, we can build a source map:

```text
RTL signal -> lowered net/cell -> source file/line -> original BLIF node candidate
```

BLIF alone may preserve some names, but it is not designed as a rich source-metadata format.
JSON is the better first inspection target.

## Why Optimization Makes This Hard

Synthesis optimization can:

- rename internal nets;
- remove wires that were only temporary expressions;
- merge equivalent logic;
- duplicate cones to improve area or delay;
- rewrite expressions into structurally different but functionally equivalent forms.

That means source mapping is not a simple string-matching problem. It should be treated as
metadata propagation plus reconstruction. The existing BLIF correspondence pipeline can help
when a lowered net survives as an original BLIF node, but deeper integration is needed when
optimization changes the structure.

## Metadata Needed for Register Suggestions

A future register-insertion suggestion should carry:

- optimized critical-path node;
- mapped original BLIF node;
- RTL signal or expression;
- source file and line;
- module hierarchy;
- mapping method and confidence;
- path position and estimated delay split;
- semantic caveats, such as latency changes and control/data dependencies.

The current iteration does not rewrite RTL and does not insert registers. It creates the
planning document, a controlled Verilog example, a Yosys metadata probe, and a source-map
prototype that gracefully skips if Yosys is unavailable.

## Next Steps

1. Run the probe on machines with Yosys installed and compare JSON versus BLIF metadata.
2. Preserve source attributes through the original BLIF generation flow.
3. Attach source-map rows to original BLIF nodes used by critical-path back-mapping.
4. Report optimized path nodes together with original source locations.
5. Only after that, prototype engineer-reviewed register insertion suggestions.
