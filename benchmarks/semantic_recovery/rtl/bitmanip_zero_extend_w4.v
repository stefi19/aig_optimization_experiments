// Generated semantic-recovery benchmark: bitmanip_zero_extend_w4
// Ground-truth expression: {{4{1'b0}}, a}
module bitmanip_zero_extend_w4(a, y);
    input [3:0] a;
    output [7:0] y;

    assign y = {{4{1'b0}}, a};
endmodule
