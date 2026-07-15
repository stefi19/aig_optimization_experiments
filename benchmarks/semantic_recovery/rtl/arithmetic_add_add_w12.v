// Generated semantic-recovery benchmark: arithmetic_add_add_w12
// Ground-truth expression: a + b + c
module arithmetic_add_add_w12(a, b, c, y);
    input [11:0] a;
    input [11:0] b;
    input [11:0] c;
    output [13:0] y;

    assign y = a + b + c;
endmodule
