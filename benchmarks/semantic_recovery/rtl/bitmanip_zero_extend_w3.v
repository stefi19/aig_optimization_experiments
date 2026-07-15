// Generated semantic-recovery benchmark: bitmanip_zero_extend_w3
// Ground-truth expression: {{3{1'b0}}, a}
module bitmanip_zero_extend_w3(a, y);
    input [2:0] a;
    output [5:0] y;

    assign y = {{3{1'b0}}, a};
endmodule
