// Generated semantic-recovery benchmark: arithmetic_multiply_accumulate_w4
// Ground-truth expression: (a * b) + c
module arithmetic_multiply_accumulate_w4(a, b, c, y);
    input [3:0] a;
    input [3:0] b;
    input [7:0] c;
    output [8:0] y;

    assign y = (a * b) + c;
endmodule
