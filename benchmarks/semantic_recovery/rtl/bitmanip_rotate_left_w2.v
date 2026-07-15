// Generated semantic-recovery benchmark: bitmanip_rotate_left_w2
// Ground-truth expression: {a[2-2:0], a[2-1]}
module bitmanip_rotate_left_w2(a, y);
    input [1:0] a;
    output [1:0] y;

    assign y = {a[2-2:0], a[2-1]};
endmodule
