// Generated semantic-recovery benchmark: bitmanip_concat_w3
// Ground-truth expression: {a, b}
module bitmanip_concat_w3(a, b, y);
    input [2:0] a;
    input [2:0] b;
    output [5:0] y;

    assign y = {a, b};
endmodule
