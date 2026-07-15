// Generated semantic-recovery benchmark: control_arithmetic_select_w4
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w4(a, b, sel, y);
    input [3:0] a;
    input [3:0] b;
    input sel;
    output [4:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
