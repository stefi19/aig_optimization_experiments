// Generated semantic-recovery benchmark: control_arithmetic_select_w8
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w8(a, b, sel, y);
    input [7:0] a;
    input [7:0] b;
    input sel;
    output [8:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
