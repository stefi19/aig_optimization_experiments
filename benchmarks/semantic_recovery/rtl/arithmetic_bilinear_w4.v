// Generated semantic-recovery benchmark: arithmetic_bilinear_w4
// Ground-truth expression: (a * b) + (c * d)
module arithmetic_bilinear_w4(a, b, c, d, y);
    input [3:0] a;
    input [3:0] b;
    input [3:0] c;
    input [3:0] d;
    output [8:0] y;

    assign y = (a * b) + (c * d);
endmodule
