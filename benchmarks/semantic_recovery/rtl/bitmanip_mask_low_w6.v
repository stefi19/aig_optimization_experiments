// Generated semantic-recovery benchmark: bitmanip_mask_low_w6
// Ground-truth expression: a & 7
module bitmanip_mask_low_w6(a, y);
    input [5:0] a;
    output [5:0] y;

    assign y = a & 7;
endmodule
