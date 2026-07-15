// Generated semantic-recovery benchmark: bitmanip_rotate_left_w6
// Ground-truth expression: {a[6-2:0], a[6-1]}
module bitmanip_rotate_left_w6(a, y);
    input [5:0] a;
    output [5:0] y;

    assign y = {a[6-2:0], a[6-1]};
endmodule
