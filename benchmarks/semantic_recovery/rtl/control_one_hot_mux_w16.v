// Generated semantic-recovery benchmark: control_one_hot_mux_w16
// Ground-truth expression: (s0 ? a : 0) | (s1 ? b : 0)
module control_one_hot_mux_w16(a, b, s0, s1, y);
    input [15:0] a;
    input [15:0] b;
    input s0;
    input s1;
    output [15:0] y;

    assign y = (s0 ? a : 0) | (s1 ? b : 0);
endmodule
