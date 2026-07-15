// Generated semantic-recovery benchmark: control_priority_mux_w16
// Ground-truth expression: s0 ? a : (s1 ? b : c)
module control_priority_mux_w16(a, b, c, s0, s1, y);
    input [15:0] a;
    input [15:0] b;
    input [15:0] c;
    input s0;
    input s1;
    output [15:0] y;

    assign y = s0 ? a : (s1 ? b : c);
endmodule
