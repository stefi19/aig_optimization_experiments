// Generated semantic-recovery benchmark: control_arithmetic_select_w16
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w16(a, b, sel, y);
    input [15:0] a;
    input [15:0] b;
    input sel;
    output [16:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
