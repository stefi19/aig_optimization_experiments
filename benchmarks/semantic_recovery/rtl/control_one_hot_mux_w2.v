// Generated semantic-recovery benchmark: control_one_hot_mux_w2
// Ground-truth expression: (s0 ? a : 0) | (s1 ? b : 0)
module control_one_hot_mux_w2(a, b, s0, s1, y);
    input [1:0] a;
    input [1:0] b;
    input s0;
    input s1;
    output [1:0] y;

    assign y = (s0 ? a : 0) | (s1 ? b : 0);
endmodule
