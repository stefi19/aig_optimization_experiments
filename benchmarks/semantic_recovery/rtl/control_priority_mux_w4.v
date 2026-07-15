// Generated semantic-recovery benchmark: control_priority_mux_w4
// Ground-truth expression: s0 ? a : (s1 ? b : c)
module control_priority_mux_w4(a, b, c, s0, s1, y);
    input [3:0] a;
    input [3:0] b;
    input [3:0] c;
    input s0;
    input s1;
    output [3:0] y;

    assign y = s0 ? a : (s1 ? b : c);
endmodule
