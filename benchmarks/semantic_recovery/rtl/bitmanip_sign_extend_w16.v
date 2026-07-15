// Generated semantic-recovery benchmark: bitmanip_sign_extend_w16
// Ground-truth expression: {{16{a[15]}}, a}
module bitmanip_sign_extend_w16(a, y);
    input signed [15:0] a;
    output signed [31:0] y;

    assign y = {{16{a[15]}}, a};
endmodule
