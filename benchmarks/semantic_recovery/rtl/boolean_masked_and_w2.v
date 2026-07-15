// Generated semantic-recovery benchmark: boolean_masked_and_w2
// Ground-truth expression: a & {2{mask}}
module boolean_masked_and_w2(a, mask, y);
    input [1:0] a;
    input mask;
    output [1:0] y;

    assign y = a & {2{mask}};
endmodule
