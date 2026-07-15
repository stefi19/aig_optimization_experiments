// Generated semantic-recovery benchmark: bitmanip_mask_low_w3
// Ground-truth expression: a & 1
module bitmanip_mask_low_w3(a, y);
    input [2:0] a;
    output [2:0] y;

    assign y = a & 1;
endmodule
