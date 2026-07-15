// Generated semantic-recovery benchmark: arithmetic_shifted_add_w4
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w4(a, b, y);
    input [3:0] a;
    input [3:0] b;
    output [5:0] y;

    assign y = a + (b << 1);
endmodule
