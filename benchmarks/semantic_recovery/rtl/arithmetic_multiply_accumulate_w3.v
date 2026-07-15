// Generated semantic-recovery benchmark: arithmetic_multiply_accumulate_w3
// Ground-truth expression: (a * b) + c
module arithmetic_multiply_accumulate_w3(a, b, c, y);
    input [2:0] a;
    input [2:0] b;
    input [5:0] c;
    output [6:0] y;

    assign y = (a * b) + c;
endmodule
