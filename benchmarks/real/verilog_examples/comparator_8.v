// comparator_8.v  –  8-bit magnitude comparator
//
// Inputs : a[7:0], b[7:0]
// Outputs: lt  (a < b)
//          eq  (a == b)
//          gt  (a > b)
//
// To convert to BLIF:
//   yosys -p "read_verilog comparator_8.v; synth -top comparator_8; write_blif comparator_8.blif"

module comparator_8 (
    input  [7:0] a,
    input  [7:0] b,
    output       lt,
    output       eq,
    output       gt
);
    assign eq = (a == b);
    assign lt = (a  < b);
    assign gt = (a  > b);
endmodule
