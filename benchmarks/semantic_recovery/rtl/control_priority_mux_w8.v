// Generated semantic-recovery benchmark: control_priority_mux_w8
// Ground-truth expression: s0 ? a : (s1 ? b : c)
module control_priority_mux_w8(a, b, c, s0, s1, y);
    input [7:0] a;
    input [7:0] b;
    input [7:0] c;
    input s0;
    input s1;
    output [7:0] y;

    assign y = s0 ? a : (s1 ? b : c);
endmodule
