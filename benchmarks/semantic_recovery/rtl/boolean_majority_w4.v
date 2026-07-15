// Generated semantic-recovery benchmark: boolean_majority_w4
// Ground-truth expression: (a & b) | (a & c) | (b & c)
module boolean_majority_w4(a, b, c, y);
    input [3:0] a;
    input [3:0] b;
    input [3:0] c;
    output [3:0] y;

    assign y = (a & b) | (a & c) | (b & c);
endmodule
