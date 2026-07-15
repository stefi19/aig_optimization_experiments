// Generated semantic-recovery benchmark: arithmetic_signed_add_w6
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w6(a, b, y);
    input signed [5:0] a;
    input signed [5:0] b;
    output signed [6:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
