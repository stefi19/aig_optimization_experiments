// Generated semantic-recovery benchmark: bitmanip_zero_extend_w8
// Ground-truth expression: {{8{1'b0}}, a}
module bitmanip_zero_extend_w8(a, y);
    input [7:0] a;
    output [15:0] y;

    assign y = {{8{1'b0}}, a};
endmodule
