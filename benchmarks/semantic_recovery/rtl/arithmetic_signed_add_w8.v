// Generated semantic-recovery benchmark: arithmetic_signed_add_w8
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w8(a, b, y);
    input signed [7:0] a;
    input signed [7:0] b;
    output signed [8:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
