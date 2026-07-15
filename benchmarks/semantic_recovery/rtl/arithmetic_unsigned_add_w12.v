// Generated semantic-recovery benchmark: arithmetic_unsigned_add_w12
// Ground-truth expression: a + b
module arithmetic_unsigned_add_w12(a, b, y);
    input [11:0] a;
    input [11:0] b;
    output [12:0] y;

    assign y = a + b;
endmodule
