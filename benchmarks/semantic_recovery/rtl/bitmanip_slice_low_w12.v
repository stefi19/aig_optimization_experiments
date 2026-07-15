// Generated semantic-recovery benchmark: bitmanip_slice_low_w12
// Ground-truth expression: a[5:0]
module bitmanip_slice_low_w12(a, y);
    input [11:0] a;
    output [5:0] y;

    assign y = a[5:0];
endmodule
