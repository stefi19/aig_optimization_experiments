// Generated semantic-recovery benchmark: control_mux2_w3
// Ground-truth expression: sel ? b : a
module control_mux2_w3(a, b, sel, y);
    input [2:0] a;
    input [2:0] b;
    input sel;
    output [2:0] y;

    assign y = sel ? b : a;
endmodule
