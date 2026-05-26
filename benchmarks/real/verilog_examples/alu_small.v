// alu_small.v  –  4-bit ALU with 4 operations
//
// Inputs : a[3:0], b[3:0]
//          op[1:0]   — 00=ADD, 01=SUB, 10=AND, 11=OR
// Outputs: result[3:0]
//          zero       (1 when result == 0)
//
// This is a realistic small datapath block that generates interesting
// internal structure under optimization (carry chains, mux trees).
//
// To convert to BLIF:
//   yosys -p "read_verilog alu_small.v; synth -top alu_small; write_blif alu_small.blif"

module alu_small (
    input  [3:0] a,
    input  [3:0] b,
    input  [1:0] op,
    output [3:0] result,
    output       zero
);
    wire [3:0] add_result = a + b;
    wire [3:0] sub_result = a - b;
    wire [3:0] and_result = a & b;
    wire [3:0] or_result  = a | b;

    assign result = (op == 2'b00) ? add_result :
                    (op == 2'b01) ? sub_result :
                    (op == 2'b10) ? and_result :
                                    or_result;

    assign zero = (result == 4'b0000);
endmodule
