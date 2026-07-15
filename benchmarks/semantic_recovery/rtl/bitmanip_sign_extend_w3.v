// Generated semantic-recovery benchmark: bitmanip_sign_extend_w3
// Ground-truth expression: {{3{a[2]}}, a}
module bitmanip_sign_extend_w3(a, y);
    input signed [2:0] a;
    output signed [5:0] y;

    assign y = {{3{a[2]}}, a};
endmodule
