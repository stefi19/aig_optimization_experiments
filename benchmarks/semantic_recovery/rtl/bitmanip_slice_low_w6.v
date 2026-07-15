// Generated semantic-recovery benchmark: bitmanip_slice_low_w6
// Ground-truth expression: a[2:0]
module bitmanip_slice_low_w6(a, y);
    input [5:0] a;
    output [2:0] y;

    assign y = a[2:0];
endmodule
