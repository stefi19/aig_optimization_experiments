// Generated semantic-recovery benchmark: control_mux2_w6
// Ground-truth expression: sel ? b : a
module control_mux2_w6(a, b, sel, y);
    input [5:0] a;
    input [5:0] b;
    input sel;
    output [5:0] y;

    assign y = sel ? b : a;
endmodule
