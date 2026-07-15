// Generated semantic-recovery benchmark: comparison_signed_lt_w16
// Ground-truth expression: $signed(a) < $signed(b)
module comparison_signed_lt_w16(a, b, y);
    input signed [15:0] a;
    input signed [15:0] b;
    output signed y;

    assign y = $signed(a) < $signed(b);
endmodule
