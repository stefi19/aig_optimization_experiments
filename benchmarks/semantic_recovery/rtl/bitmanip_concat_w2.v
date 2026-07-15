// Generated semantic-recovery benchmark: bitmanip_concat_w2
// Ground-truth expression: {a, b}
module bitmanip_concat_w2(a, b, y);
    input [1:0] a;
    input [1:0] b;
    output [3:0] y;

    assign y = {a, b};
endmodule
