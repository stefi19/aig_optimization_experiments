// Generated semantic-recovery benchmark: bitmanip_zero_extend_w2
// Ground-truth expression: {{2{1'b0}}, a}
module bitmanip_zero_extend_w2(a, y);
    input [1:0] a;
    output [3:0] y;

    assign y = {{2{1'b0}}, a};
endmodule
