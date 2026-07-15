// Generated semantic-recovery benchmark: control_one_hot_mux_w8
// Ground-truth expression: (s0 ? a : 0) | (s1 ? b : 0)
module control_one_hot_mux_w8(a, b, s0, s1, y);
    input [7:0] a;
    input [7:0] b;
    input s0;
    input s1;
    output [7:0] y;

    assign y = (s0 ? a : 0) | (s1 ? b : 0);
endmodule
