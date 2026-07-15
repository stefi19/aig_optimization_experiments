// Generated semantic-recovery benchmark: control_mux2_w4
// Ground-truth expression: sel ? b : a
module control_mux2_w4(a, b, sel, y);
    input [3:0] a;
    input [3:0] b;
    input sel;
    output [3:0] y;

    assign y = sel ? b : a;
endmodule
