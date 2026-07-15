// Generated semantic-recovery benchmark: bitmanip_concat_w4
// Ground-truth expression: {a, b}
module bitmanip_concat_w4(a, b, y);
    input [3:0] a;
    input [3:0] b;
    output [7:0] y;

    assign y = {a, b};
endmodule
