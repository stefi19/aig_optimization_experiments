// Generated semantic-recovery benchmark: boolean_bitwise_xnor_w16
// Ground-truth expression: ~(a ^ b)
module boolean_bitwise_xnor_w16(a, b, y);
    input [15:0] a;
    input [15:0] b;
    output [15:0] y;

    assign y = ~(a ^ b);
endmodule
