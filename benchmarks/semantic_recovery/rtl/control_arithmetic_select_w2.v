// Generated semantic-recovery benchmark: control_arithmetic_select_w2
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w2(a, b, sel, y);
    input [1:0] a;
    input [1:0] b;
    input sel;
    output [2:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
