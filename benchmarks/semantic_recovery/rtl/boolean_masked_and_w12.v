// Generated semantic-recovery benchmark: boolean_masked_and_w12
// Ground-truth expression: a & {12{mask}}
module boolean_masked_and_w12(a, mask, y);
    input [11:0] a;
    input mask;
    output [11:0] y;

    assign y = a & {12{mask}};
endmodule
