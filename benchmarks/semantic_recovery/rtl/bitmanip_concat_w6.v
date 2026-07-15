// Generated semantic-recovery benchmark: bitmanip_concat_w6
// Ground-truth expression: {a, b}
module bitmanip_concat_w6(a, b, y);
    input [5:0] a;
    input [5:0] b;
    output [11:0] y;

    assign y = {a, b};
endmodule
