// Generated semantic-recovery benchmark: bitmanip_slice_low_w8
// Ground-truth expression: a[3:0]
module bitmanip_slice_low_w8(a, y);
    input [7:0] a;
    output [3:0] y;

    assign y = a[3:0];
endmodule
