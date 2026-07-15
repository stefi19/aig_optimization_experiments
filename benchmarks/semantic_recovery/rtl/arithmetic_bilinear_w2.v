// Generated semantic-recovery benchmark: arithmetic_bilinear_w2
// Ground-truth expression: (a * b) + (c * d)
module arithmetic_bilinear_w2(a, b, c, d, y);
    input [1:0] a;
    input [1:0] b;
    input [1:0] c;
    input [1:0] d;
    output [4:0] y;

    assign y = (a * b) + (c * d);
endmodule
