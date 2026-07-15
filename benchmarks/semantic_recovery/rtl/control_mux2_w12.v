// Generated semantic-recovery benchmark: control_mux2_w12
// Ground-truth expression: sel ? b : a
module control_mux2_w12(a, b, sel, y);
    input [11:0] a;
    input [11:0] b;
    input sel;
    output [11:0] y;

    assign y = sel ? b : a;
endmodule
