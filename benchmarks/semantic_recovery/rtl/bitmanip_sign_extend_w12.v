// Generated semantic-recovery benchmark: bitmanip_sign_extend_w12
// Ground-truth expression: {{12{a[11]}}, a}
module bitmanip_sign_extend_w12(a, y);
    input signed [11:0] a;
    output signed [23:0] y;

    assign y = {{12{a[11]}}, a};
endmodule
