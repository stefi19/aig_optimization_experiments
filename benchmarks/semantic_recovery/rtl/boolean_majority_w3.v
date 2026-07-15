// Generated semantic-recovery benchmark: boolean_majority_w3
// Ground-truth expression: (a & b) | (a & c) | (b & c)
module boolean_majority_w3(a, b, c, y);
    input [2:0] a;
    input [2:0] b;
    input [2:0] c;
    output [2:0] y;

    assign y = (a & b) | (a & c) | (b & c);
endmodule
