// Generated semantic-recovery benchmark: control_mux2_w16
// Ground-truth expression: sel ? b : a
module control_mux2_w16(a, b, sel, y);
    input [15:0] a;
    input [15:0] b;
    input sel;
    output [15:0] y;

    assign y = sel ? b : a;
endmodule
