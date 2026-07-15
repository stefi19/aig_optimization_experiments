// Generated semantic-recovery benchmark: boolean_masked_xor_w8
// Ground-truth expression: a ^ {8{mask}}
module boolean_masked_xor_w8(a, mask, y);
    input [7:0] a;
    input mask;
    output [7:0] y;

    assign y = a ^ {8{mask}};
endmodule
