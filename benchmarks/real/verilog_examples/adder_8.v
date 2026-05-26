// adder_8.v  –  8-bit ripple-carry adder
//
// Inputs : a[7:0], b[7:0], cin
// Outputs: sum[7:0], cout
//
// This is the Verilog source for the benchmark.
// To convert to BLIF for use with ABC run:
//   yosys -p "read_verilog adder_8.v; synth -top adder_8; write_blif adder_8.blif"
// or use the helper script:
//   python3 scripts/import_real_benchmarks.py --verilog benchmarks/real/verilog_examples/

module adder_8 (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    wire [8:0] carry;
    assign carry[0] = cin;

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : fa
            assign sum[i]     = a[i] ^ b[i] ^ carry[i];
            assign carry[i+1] = (a[i] & b[i]) | (a[i] & carry[i]) | (b[i] & carry[i]);
        end
    endgenerate

    assign cout = carry[8];
endmodule
