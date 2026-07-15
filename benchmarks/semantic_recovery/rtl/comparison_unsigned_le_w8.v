// Generated semantic-recovery benchmark: comparison_unsigned_le_w8
// Ground-truth expression: a <= b
module comparison_unsigned_le_w8(a, b, y);
    input [7:0] a;
    input [7:0] b;
    output y;

    assign y = a <= b;
endmodule
