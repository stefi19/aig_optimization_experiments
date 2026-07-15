// Generated semantic-recovery benchmark: bitmanip_slice_low_w16
// Ground-truth expression: a[7:0]
module bitmanip_slice_low_w16(a, y);
    input [15:0] a;
    output [7:0] y;

    assign y = a[7:0];
endmodule
