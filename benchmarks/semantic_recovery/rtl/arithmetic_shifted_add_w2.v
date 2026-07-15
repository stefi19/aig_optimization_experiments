// Generated semantic-recovery benchmark: arithmetic_shifted_add_w2
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w2(a, b, y);
    input [1:0] a;
    input [1:0] b;
    output [3:0] y;

    assign y = a + (b << 1);
endmodule
