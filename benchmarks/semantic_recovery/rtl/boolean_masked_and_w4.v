// Generated semantic-recovery benchmark: boolean_masked_and_w4
// Ground-truth expression: a & {4{mask}}
module boolean_masked_and_w4(a, mask, y);
    input [3:0] a;
    input mask;
    output [3:0] y;

    assign y = a & {4{mask}};
endmodule
