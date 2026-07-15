// Generated semantic-recovery benchmark: control_priority_mux_w2
// Ground-truth expression: s0 ? a : (s1 ? b : c)
module control_priority_mux_w2(a, b, c, s0, s1, y);
    input [1:0] a;
    input [1:0] b;
    input [1:0] c;
    input s0;
    input s1;
    output [1:0] y;

    assign y = s0 ? a : (s1 ? b : c);
endmodule
