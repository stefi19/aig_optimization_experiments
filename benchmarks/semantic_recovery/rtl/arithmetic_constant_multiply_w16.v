// Generated semantic-recovery benchmark: arithmetic_constant_multiply_w16
// Ground-truth expression: a * 3
module arithmetic_constant_multiply_w16(a, y);
    input [15:0] a;
    output [17:0] y;

    assign y = a * 3;
endmodule
