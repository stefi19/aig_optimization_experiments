// Generated semantic-recovery benchmark: control_arithmetic_select_w6
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w6(a, b, sel, y);
    input [5:0] a;
    input [5:0] b;
    input sel;
    output [6:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
