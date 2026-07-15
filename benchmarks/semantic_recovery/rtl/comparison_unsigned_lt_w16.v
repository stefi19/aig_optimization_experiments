// Generated semantic-recovery benchmark: comparison_unsigned_lt_w16
// Ground-truth expression: a < b
module comparison_unsigned_lt_w16(a, b, y);
    input [15:0] a;
    input [15:0] b;
    output y;

    assign y = a < b;
endmodule
