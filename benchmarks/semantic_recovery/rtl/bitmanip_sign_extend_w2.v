// Generated semantic-recovery benchmark: bitmanip_sign_extend_w2
// Ground-truth expression: {{2{a[1]}}, a}
module bitmanip_sign_extend_w2(a, y);
    input signed [1:0] a;
    output signed [3:0] y;

    assign y = {{2{a[1]}}, a};
endmodule
