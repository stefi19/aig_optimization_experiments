// Generated semantic-recovery benchmark: arithmetic_add_add_w8
// Ground-truth expression: a + b + c
module arithmetic_add_add_w8(a, b, c, y);
    input [7:0] a;
    input [7:0] b;
    input [7:0] c;
    output [9:0] y;

    assign y = a + b + c;
endmodule
