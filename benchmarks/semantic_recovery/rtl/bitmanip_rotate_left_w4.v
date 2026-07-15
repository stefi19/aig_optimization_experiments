// Generated semantic-recovery benchmark: bitmanip_rotate_left_w4
// Ground-truth expression: {a[4-2:0], a[4-1]}
module bitmanip_rotate_left_w4(a, y);
    input [3:0] a;
    output [3:0] y;

    assign y = {a[4-2:0], a[4-1]};
endmodule
