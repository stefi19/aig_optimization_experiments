// Generated semantic-recovery benchmark: bitmanip_rotate_left_w3
// Ground-truth expression: {a[3-2:0], a[3-1]}
module bitmanip_rotate_left_w3(a, y);
    input [2:0] a;
    output [2:0] y;

    assign y = {a[3-2:0], a[3-1]};
endmodule
