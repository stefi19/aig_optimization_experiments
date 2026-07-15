// Generated semantic-recovery benchmark: arithmetic_mixed_width_add_w4
// Ground-truth expression: a + b
module arithmetic_mixed_width_add_w4(a, b, y);
    input [3:0] a;
    input [2:0] b;
    output [4:0] y;

    assign y = a + b;
endmodule
