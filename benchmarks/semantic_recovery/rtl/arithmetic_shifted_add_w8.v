// Generated semantic-recovery benchmark: arithmetic_shifted_add_w8
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w8(a, b, y);
    input [7:0] a;
    input [7:0] b;
    output [9:0] y;

    assign y = a + (b << 1);
endmodule
