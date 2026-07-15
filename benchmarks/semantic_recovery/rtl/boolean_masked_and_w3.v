// Generated semantic-recovery benchmark: boolean_masked_and_w3
// Ground-truth expression: a & {3{mask}}
module boolean_masked_and_w3(a, mask, y);
    input [2:0] a;
    input mask;
    output [2:0] y;

    assign y = a & {3{mask}};
endmodule
