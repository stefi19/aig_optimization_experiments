// Generated semantic-recovery benchmark: arithmetic_shifted_add_w16
// Ground-truth expression: a + (b << 1)
module arithmetic_shifted_add_w16(a, b, y);
    input [15:0] a;
    input [15:0] b;
    output [17:0] y;

    assign y = a + (b << 1);
endmodule
