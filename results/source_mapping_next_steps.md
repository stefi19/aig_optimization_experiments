# Source Mapping Next Steps

The current back-mapping pipeline explains optimized BLIF nodes in terms of original BLIF nodes.
The next engineering layer is to attach source metadata to those original nodes:

```text
optimized path node
  -> original BLIF node
  -> RTL signal / expression / source location
  -> engineer-reviewed register insertion suggestion
```

Required follow-up work:

- preserve Yosys `src` attributes and signal names during original BLIF generation;
- relate Yosys JSON netnames/cells to BLIF `.names` outputs;
- propagate mapping confidence from exact signature, SAT/CEC-proven, and approximate layers;
- report source locations on critical-path rows;
- verify any future register insertion with sequential equivalence or an explicit latency contract.
