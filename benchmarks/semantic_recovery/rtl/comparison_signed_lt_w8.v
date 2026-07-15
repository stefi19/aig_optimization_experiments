// Generated semantic-recovery benchmark: comparison_signed_lt_w8
// Ground-truth expression: $signed(a) < $signed(b)
module comparison_signed_lt_w8(a, b, y);
    input signed [7:0] a;
    input signed [7:0] b;
    output signed y;

    assign y = $signed(a) < $signed(b);
endmodule
