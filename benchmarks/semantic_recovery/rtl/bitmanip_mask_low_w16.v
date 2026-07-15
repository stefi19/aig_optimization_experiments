// Generated semantic-recovery benchmark: bitmanip_mask_low_w16
// Ground-truth expression: a & 255
module bitmanip_mask_low_w16(a, y);
    input [15:0] a;
    output [15:0] y;

    assign y = a & 255;
endmodule
