// Generated semantic-recovery benchmark: bitmanip_concat_w8
// Ground-truth expression: {a, b}
module bitmanip_concat_w8(a, b, y);
    input [7:0] a;
    input [7:0] b;
    output [15:0] y;

    assign y = {a, b};
endmodule
