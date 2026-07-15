// Generated semantic-recovery benchmark: arithmetic_sub_w8
// Ground-truth expression: a - b
module arithmetic_sub_w8(a, b, y);
    input [7:0] a;
    input [7:0] b;
    output [8:0] y;

    assign y = a - b;
endmodule
