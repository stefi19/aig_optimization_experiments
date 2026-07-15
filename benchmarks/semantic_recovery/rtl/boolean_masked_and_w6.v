// Generated semantic-recovery benchmark: boolean_masked_and_w6
// Ground-truth expression: a & {6{mask}}
module boolean_masked_and_w6(a, mask, y);
    input [5:0] a;
    input mask;
    output [5:0] y;

    assign y = a & {6{mask}};
endmodule
