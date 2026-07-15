// Generated semantic-recovery benchmark: arithmetic_add_add_w16
// Ground-truth expression: a + b + c
module arithmetic_add_add_w16(a, b, c, y);
    input [15:0] a;
    input [15:0] b;
    input [15:0] c;
    output [17:0] y;

    assign y = a + b + c;
endmodule
