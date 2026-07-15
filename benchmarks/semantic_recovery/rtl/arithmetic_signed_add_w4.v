// Generated semantic-recovery benchmark: arithmetic_signed_add_w4
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w4(a, b, y);
    input signed [3:0] a;
    input signed [3:0] b;
    output signed [4:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
