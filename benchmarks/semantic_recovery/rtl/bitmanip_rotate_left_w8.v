// Generated semantic-recovery benchmark: bitmanip_rotate_left_w8
// Ground-truth expression: {a[8-2:0], a[8-1]}
module bitmanip_rotate_left_w8(a, y);
    input [7:0] a;
    output [7:0] y;

    assign y = {a[8-2:0], a[8-1]};
endmodule
