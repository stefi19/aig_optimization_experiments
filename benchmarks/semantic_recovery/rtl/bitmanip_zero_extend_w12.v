// Generated semantic-recovery benchmark: bitmanip_zero_extend_w12
// Ground-truth expression: {{12{1'b0}}, a}
module bitmanip_zero_extend_w12(a, y);
    input [11:0] a;
    output [23:0] y;

    assign y = {{12{1'b0}}, a};
endmodule
