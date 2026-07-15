// Generated semantic-recovery benchmark: arithmetic_shifted_add_w12
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w12(a, b, y);
    input [11:0] a;
    input [11:0] b;
    output [13:0] y;

    assign y = a + (b << 1);
endmodule
