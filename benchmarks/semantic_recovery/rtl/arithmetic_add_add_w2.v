// Generated semantic-recovery benchmark: arithmetic_add_add_w2
// Ground-truth expression: a + b + c
module arithmetic_add_add_w2(a, b, c, y);
    input [1:0] a;
    input [1:0] b;
    input [1:0] c;
    output [3:0] y;

    assign y = a + b + c;
endmodule
