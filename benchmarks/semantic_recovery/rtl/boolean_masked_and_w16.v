// Generated semantic-recovery benchmark: boolean_masked_and_w16
// Ground-truth expression: a & {16{mask}}
module boolean_masked_and_w16(a, mask, y);
    input [15:0] a;
    input mask;
    output [15:0] y;

    assign y = a & {16{mask}};
endmodule
