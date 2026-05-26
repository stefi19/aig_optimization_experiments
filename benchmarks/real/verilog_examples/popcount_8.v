// popcount_8.v  –  8-bit population count (count number of 1-bits)
//
// Inputs : d[7:0]
// Outputs: count[3:0]   (0–8 encoded in 4 bits)
//
// To convert to BLIF:
//   yosys -p "read_verilog popcount_8.v; synth -top popcount_8; write_blif popcount_8.blif"

module popcount_8 (
    input  [7:0] d,
    output [3:0] count
);
    // Carry-save adder tree
    wire [1:0] s0, s1, s2, s3;
    wire [1:0] t0, t1;
    wire [2:0] u0;

    // First level: 4 half-adders on pairs
    assign s0 = d[0] + d[1];
    assign s1 = d[2] + d[3];
    assign s2 = d[4] + d[5];
    assign s3 = d[6] + d[7];

    // Second level
    assign t0 = s0 + s1;
    assign t1 = s2 + s3;

    // Third level
    assign u0 = t0 + t1;

    assign count = u0;
endmodule
