// Generated semantic-recovery benchmark: bitmanip_zero_extend_w6
// Ground-truth expression: {{6{1'b0}}, a}
module bitmanip_zero_extend_w6(a, y);
    input [5:0] a;
    output [11:0] y;

    assign y = {{6{1'b0}}, a};
endmodule
