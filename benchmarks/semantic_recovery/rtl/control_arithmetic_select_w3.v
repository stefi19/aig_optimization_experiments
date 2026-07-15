// Generated semantic-recovery benchmark: control_arithmetic_select_w3
// Ground-truth expression: sel ? (a + b) : (a ^ b)
module control_arithmetic_select_w3(a, b, sel, y);
    input [2:0] a;
    input [2:0] b;
    input sel;
    output [3:0] y;

    assign y = sel ? (a + b) : (a ^ b);
endmodule
