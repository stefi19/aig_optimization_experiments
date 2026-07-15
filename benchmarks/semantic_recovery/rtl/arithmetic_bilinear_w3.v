// Generated semantic-recovery benchmark: arithmetic_bilinear_w3
// Ground-truth expression: (a * b) + (c * d)
module arithmetic_bilinear_w3(a, b, c, d, y);
    input [2:0] a;
    input [2:0] b;
    input [2:0] c;
    input [2:0] d;
    output [6:0] y;

    assign y = (a * b) + (c * d);
endmodule
