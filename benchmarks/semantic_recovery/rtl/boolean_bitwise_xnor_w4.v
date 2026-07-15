// Generated semantic-recovery benchmark: boolean_bitwise_xnor_w4
// Ground-truth expression: ~(a ^ b)
module boolean_bitwise_xnor_w4(a, b, y);
    input [3:0] a;
    input [3:0] b;
    output [3:0] y;

    assign y = ~(a ^ b);
endmodule
