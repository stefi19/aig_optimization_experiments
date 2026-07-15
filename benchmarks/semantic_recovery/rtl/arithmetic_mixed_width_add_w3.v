// Generated semantic-recovery benchmark: arithmetic_mixed_width_add_w3
// Ground-truth expression: a + b
module arithmetic_mixed_width_add_w3(a, b, y);
    input [2:0] a;
    input [1:0] b;
    output [3:0] y;

    assign y = a + b;
endmodule
