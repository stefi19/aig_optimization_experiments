// Generated semantic-recovery benchmark: control_mux2_w2
// Ground-truth expression: sel ? b : a
module control_mux2_w2(a, b, sel, y);
    input [1:0] a;
    input [1:0] b;
    input sel;
    output [1:0] y;

    assign y = sel ? b : a;
endmodule
