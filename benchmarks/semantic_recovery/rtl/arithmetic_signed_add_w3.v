// Generated semantic-recovery benchmark: arithmetic_signed_add_w3
// Ground-truth expression: $signed(a) + $signed(b)
module arithmetic_signed_add_w3(a, b, y);
    input signed [2:0] a;
    input signed [2:0] b;
    output signed [3:0] y;

    assign y = $signed(a) + $signed(b);
endmodule
