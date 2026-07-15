// Generated semantic-recovery benchmark: bitmanip_mask_low_w8
// Ground-truth expression: a & 15
module bitmanip_mask_low_w8(a, y);
    input [7:0] a;
    output [7:0] y;

    assign y = a & 15;
endmodule
