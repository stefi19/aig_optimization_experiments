// Generated semantic-recovery benchmark: boolean_bitwise_xnor_w6
// Ground-truth expression: ~(a ^ b)
module boolean_bitwise_xnor_w6(a, b, y);
    input [5:0] a;
    input [5:0] b;
    output [5:0] y;

    assign y = ~(a ^ b);
endmodule
