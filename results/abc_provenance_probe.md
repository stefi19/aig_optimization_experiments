# ABC Provenance Investigation

ABC binary: `.abc_build/abc_repo/abc`

This probe asks a narrow question: does the local ABC build expose old-to-new
node provenance or equivalence classes through ordinary FRAIG/sweeping commands?

## Summary

- Supported investigated flows/commands: `amp_fraig_x`, `cec_self`, `dump_equiv_self`, `fraig`, `print_fanio`
- Unsupported or failed flows/commands: `choice`, `fraig -x`, `fraig -y`, `print_factor`, `print_gates`
- Rows with any sampled internal node names surviving in written BLIF: 2 / 16
- Rows that visibly exposed equivalence classes/provenance: 1 / 16
- Rows where FRAIG reduced the measured network: 2

## Controlled examples

| Example | Flow | Supported | Nodes before -> after | Names survived | Merge info visible | Equiv classes exposed | Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `duplicate_and` | `fraig` | true | 2 -> 2 | 0/2 | false | false | Two internal nodes compute the same AND function.; expected internal node names did not survive in written BLIF; no visible merge/provenance details in stdout |
| `duplicate_and` | `amp_fraig_x` | true | 2 -> 2 | 0/2 | false | false | Two internal nodes compute the same AND function.; expected internal node names did not survive in written BLIF; no visible merge/provenance details in stdout |
| `commuted_and` | `fraig` | true | 2 -> 2 | 0/2 | false | false | Two internal nodes compute a commuted AND function.; expected internal node names did not survive in written BLIF; no visible merge/provenance details in stdout |
| `commuted_and` | `amp_fraig_x` | true | 2 -> 2 | 0/2 | false | false | Two internal nodes compute a commuted AND function.; expected internal node names did not survive in written BLIF; no visible merge/provenance details in stdout |
| `same_support_nonequiv` | `fraig` | true | 3 -> 3 | 0/2 | false | false | Same support, but AND and OR are not equivalent.; expected internal node names did not survive in written BLIF; no visible merge/provenance details in stdout |
| `same_support_nonequiv` | `amp_fraig_x` | true | 3 -> 3 | 0/2 | false | false | Same support, but AND and OR are not equivalent.; expected internal node names did not survive in written BLIF; no visible merge/provenance details in stdout |

## Real benchmark sample

| Benchmark | Optimization | Flow | Supported | Nodes before -> after | Names survived | Equiv classes exposed | Notes |
|---|---|---|---:|---:|---:|---:|---|
| `external_iscas85_c432` | `rewrite` | `fraig` | true | 194 -> 170 | 50/50 | false | Light real benchmark probe; sampled first 50 optimized internal names.; surviving names: new_n44, new_n45, new_n46, new_n47, new_n48, new_n49, new_n50, new_n51, new_n52, new_n53, new_n54, new_n55, new_n56, new_n57, new_n58, new_n59, G426, new_n61, new_n62, new_n63, new_n64, new_n65, new_n66, new_n67, new_n68, new_n69, new_n70, new_n71, new_n72, new_n73, new_n74, new_n75, new_n76, new_n77, new_n78, new_n79, new_n80, new_n81, new_n82, new_n83, new_n84, new_n85, new_n86, new_n87, new_n88, new_n89, new_n90, new_n91, new_n92, new_n93; no visible merge/provenance details in stdout |
| `external_iscas85_c432` | `rewrite` | `amp_fraig_x` | true | 194 -> 170 | 50/50 | false | Light real benchmark probe; sampled first 50 optimized internal names.; surviving names: new_n44, new_n45, new_n46, new_n47, new_n48, new_n49, new_n50, new_n51, new_n52, new_n53, new_n54, new_n55, new_n56, new_n57, new_n58, new_n59, G426, new_n61, new_n62, new_n63, new_n64, new_n65, new_n66, new_n67, new_n68, new_n69, new_n70, new_n71, new_n72, new_n73, new_n74, new_n75, new_n76, new_n77, new_n78, new_n79, new_n80, new_n81, new_n82, new_n83, new_n84, new_n85, new_n86, new_n87, new_n88, new_n89, new_n90, new_n91, new_n92, new_n93; no visible merge/provenance details in stdout |

## Interpretation

ABC-native FRAIG remains useful as a standard reduction baseline, but these
ordinary command outputs do not provide the explicit old-node to new-node
mapping needed by the critical-path back-mapping prototype. Written BLIFs may
preserve some primary-output names, but internal provenance is not a reliable
correspondence interface.
