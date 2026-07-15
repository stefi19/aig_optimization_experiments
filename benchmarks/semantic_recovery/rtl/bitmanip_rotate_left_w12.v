// Generated semantic-recovery benchmark: bitmanip_rotate_left_w12
// Ground-truth expression: {a[12-2:0], a[12-1]}
module bitmanip_rotate_left_w12(a, y);
    input [11:0] a;
    output [11:0] y;

    assign y = {a[12-2:0], a[12-1]};
endmodule
