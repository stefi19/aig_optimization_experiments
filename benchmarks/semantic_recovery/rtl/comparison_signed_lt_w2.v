// Generated semantic-recovery benchmark: comparison_signed_lt_w2
// Ground-truth expression: $signed(a) < $signed(b)
module comparison_signed_lt_w2(a, b, y);
    input signed [1:0] a;
    input signed [1:0] b;
    output signed y;

    assign y = $signed(a) < $signed(b);
endmodule
