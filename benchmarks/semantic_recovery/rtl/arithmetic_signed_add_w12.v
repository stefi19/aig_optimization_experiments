// Generated semantic-recovery benchmark: arithmetic_signed_add_w12
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w12(a, b, y);
    input signed [11:0] a;
    input signed [11:0] b;
    output signed [12:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
