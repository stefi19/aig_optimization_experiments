// Generated semantic-recovery benchmark: bitmanip_concat_w12
// Ground-truth expression: {a, b}
module bitmanip_concat_w12(a, b, y);
    input [11:0] a;
    input [11:0] b;
    output [23:0] y;

    assign y = {a, b};
endmodule
