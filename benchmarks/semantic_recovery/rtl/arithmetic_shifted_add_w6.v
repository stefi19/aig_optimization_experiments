// Generated semantic-recovery benchmark: arithmetic_shifted_add_w6
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w6(a, b, y);
    input [5:0] a;
    input [5:0] b;
    output [7:0] y;

    assign y = a + (b << 1);
endmodule
