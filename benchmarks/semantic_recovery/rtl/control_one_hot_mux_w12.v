// Generated semantic-recovery benchmark: control_one_hot_mux_w12
// Ground-truth expression: (s0 ? a : 0) | (s1 ? b : 0)
module control_one_hot_mux_w12(a, b, s0, s1, y);
    input [11:0] a;
    input [11:0] b;
    input s0;
    input s1;
    output [11:0] y;

    assign y = (s0 ? a : 0) | (s1 ? b : 0);
endmodule
