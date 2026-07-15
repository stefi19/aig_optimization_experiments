// Generated semantic-recovery benchmark: control_mux2_w8
// Ground-truth expression: sel ? b : a
module control_mux2_w8(a, b, sel, y);
    input [7:0] a;
    input [7:0] b;
    input sel;
    output [7:0] y;

    assign y = sel ? b : a;
endmodule
