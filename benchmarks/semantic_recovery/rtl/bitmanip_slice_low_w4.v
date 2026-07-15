// Generated semantic-recovery benchmark: bitmanip_slice_low_w4
// Ground-truth expression: a[1:0]
module bitmanip_slice_low_w4(a, y);
    input [3:0] a;
    output [1:0] y;

    assign y = a[1:0];
endmodule
