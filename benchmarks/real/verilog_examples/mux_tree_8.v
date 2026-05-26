// mux_tree_8.v  –  8-to-1 multiplexer built as a balanced tree
//
// Inputs : d[7:0]    (8 data inputs)
//          sel[2:0]  (3-bit selector)
// Output : y
//
// Interesting for correspondence experiments because balanced tree vs.
// linear chain implementations have very different internal structures.
//
// To convert to BLIF:
//   yosys -p "read_verilog mux_tree_8.v; synth -top mux_tree_8; write_blif mux_tree_8.blif"

module mux_tree_8 (
    input  [7:0] d,
    input  [2:0] sel,
    output       y
);
    // Level 1: 4 two-to-one muxes
    wire l1_0 = sel[0] ? d[1] : d[0];
    wire l1_1 = sel[0] ? d[3] : d[2];
    wire l1_2 = sel[0] ? d[5] : d[4];
    wire l1_3 = sel[0] ? d[7] : d[6];

    // Level 2: 2 two-to-one muxes
    wire l2_0 = sel[1] ? l1_1 : l1_0;
    wire l2_1 = sel[1] ? l1_3 : l1_2;

    // Level 3: final mux
    assign y = sel[2] ? l2_1 : l2_0;
endmodule
