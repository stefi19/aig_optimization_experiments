// Generated semantic-recovery benchmark: arithmetic_add_add_w3
// Ground-truth expression: a + b + c
module arithmetic_add_add_w3(a, b, c, y);
    input [2:0] a;
    input [2:0] b;
    input [2:0] c;
    output [4:0] y;

    assign y = a + b + c;
endmodule
