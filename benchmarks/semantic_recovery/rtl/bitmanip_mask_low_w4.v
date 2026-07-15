// Generated semantic-recovery benchmark: bitmanip_mask_low_w4
// Ground-truth expression: a & 3
module bitmanip_mask_low_w4(a, y);
    input [3:0] a;
    output [3:0] y;

    assign y = a & 3;
endmodule
