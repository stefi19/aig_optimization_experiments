// Generated semantic-recovery benchmark: bitmanip_shift_left_w16
// Ground-truth expression: a << 1
module bitmanip_shift_left_w16(a, y);
    input [15:0] a;
    output [15:0] y;

    assign y = a << 1;
endmodule
