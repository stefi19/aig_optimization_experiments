// Generated semantic-recovery benchmark: bitmanip_mask_low_w12
// Ground-truth expression: a & 63
module bitmanip_mask_low_w12(a, y);
    input [11:0] a;
    output [11:0] y;

    assign y = a & 63;
endmodule
