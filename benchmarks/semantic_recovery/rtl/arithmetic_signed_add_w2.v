// Generated semantic-recovery benchmark: arithmetic_signed_add_w2
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w2(a, b, y);
    input signed [1:0] a;
    input signed [1:0] b;
    output signed [2:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
