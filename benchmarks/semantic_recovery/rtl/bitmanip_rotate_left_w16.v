// Generated semantic-recovery benchmark: bitmanip_rotate_left_w16
// Ground-truth expression: {a[16-2:0], a[16-1]}
module bitmanip_rotate_left_w16(a, y);
    input [15:0] a;
    output [15:0] y;

    assign y = {a[16-2:0], a[16-1]};
endmodule
