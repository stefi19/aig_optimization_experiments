// Generated semantic-recovery benchmark: control_arithmetic_select_w12
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w12(a, b, sel, y);
    input [11:0] a;
    input [11:0] b;
    input sel;
    output [12:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
