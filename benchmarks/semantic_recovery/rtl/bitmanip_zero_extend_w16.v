// Generated semantic-recovery benchmark: bitmanip_zero_extend_w16
// Ground-truth expression: {{16{1'b0}}, a}
module bitmanip_zero_extend_w16(a, y);
    input [15:0] a;
    output [31:0] y;

    assign y = {{16{1'b0}}, a};
endmodule
