// Generated semantic-recovery benchmark: arithmetic_reversed_sub_w12
// Ground-truth expression: b - a
module arithmetic_reversed_sub_w12(a, b, y);
    input [11:0] a;
    input [11:0] b;
    output [12:0] y;

    assign y = b - a;
endmodule
