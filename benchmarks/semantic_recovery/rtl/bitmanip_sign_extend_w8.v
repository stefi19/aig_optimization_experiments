// Generated semantic-recovery benchmark: bitmanip_sign_extend_w8
// Ground-truth expression: {{8{a[7]}}, a}
module bitmanip_sign_extend_w8(a, y);
    input signed [7:0] a;
    output signed [15:0] y;

    assign y = {{8{a[7]}}, a};
endmodule
