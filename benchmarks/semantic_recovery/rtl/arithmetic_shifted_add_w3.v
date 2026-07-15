// Generated semantic-recovery benchmark: arithmetic_shifted_add_w3
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w3(a, b, y);
    input [2:0] a;
    input [2:0] b;
    output [4:0] y;

    assign y = a + (b << 1);
endmodule
