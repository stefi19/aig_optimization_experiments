// Generated semantic-recovery benchmark: boolean_bitwise_xnor_w8
// Ground-truth expression: ~(a ^ b)
module boolean_bitwise_xnor_w8(a, b, y);
    input [7:0] a;
    input [7:0] b;
    output [7:0] y;

    assign y = ~(a ^ b);
endmodule
