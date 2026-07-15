// Generated semantic-recovery benchmark: arithmetic_signed_add_w16
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w16(a, b, y);
    input signed [15:0] a;
    input signed [15:0] b;
    output signed [16:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
