// Generated semantic-recovery benchmark: boolean_majority_w8
// Ground-truth expression: (a & b) | (a & c) | (b & c)
module boolean_majority_w8(a, b, c, y);
    input [7:0] a;
    input [7:0] b;
    input [7:0] c;
    output [7:0] y;

    assign y = (a & b) | (a & c) | (b & c);
endmodule
