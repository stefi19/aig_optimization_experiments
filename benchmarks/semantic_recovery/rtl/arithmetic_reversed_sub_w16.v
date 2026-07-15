// Generated semantic-recovery benchmark: arithmetic_reversed_sub_w16
// Ground-truth expression: b - a
module arithmetic_reversed_sub_w16(a, b, y);
    input [15:0] a;
    input [15:0] b;
    output [16:0] y;

    assign y = b - a;
endmodule
