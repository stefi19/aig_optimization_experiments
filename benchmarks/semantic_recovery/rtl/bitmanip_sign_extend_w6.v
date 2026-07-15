// Generated semantic-recovery benchmark: bitmanip_sign_extend_w6
// Ground-truth expression: {{6{a[5]}}, a}
module bitmanip_sign_extend_w6(a, y);
    input signed [5:0] a;
    output signed [11:0] y;

    assign y = {{6{a[5]}}, a};
endmodule
