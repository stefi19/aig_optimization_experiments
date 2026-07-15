// Generated semantic-recovery benchmark: bitmanip_shift_left_w8
// Ground-truth expression: a << 1
module bitmanip_shift_left_w8(a, y);
    input [7:0] a;
    output [7:0] y;

    assign y = a << 1;
endmodule
