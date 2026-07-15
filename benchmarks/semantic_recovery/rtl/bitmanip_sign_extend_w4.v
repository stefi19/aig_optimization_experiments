// Generated semantic-recovery benchmark: bitmanip_sign_extend_w4
// Ground-truth expression: {{4{a[3]}}, a}
module bitmanip_sign_extend_w4(a, y);
    input signed [3:0] a;
    output signed [7:0] y;

    assign y = {{4{a[3]}}, a};
endmodule
