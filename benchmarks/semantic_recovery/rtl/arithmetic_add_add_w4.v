// Generated semantic-recovery benchmark: arithmetic_add_add_w4
// Ground-truth expression: a + b + c
module arithmetic_add_add_w4(a, b, c, y);
    input [3:0] a;
    input [3:0] b;
    input [3:0] c;
    output [5:0] y;

    assign y = a + b + c;
endmodule
