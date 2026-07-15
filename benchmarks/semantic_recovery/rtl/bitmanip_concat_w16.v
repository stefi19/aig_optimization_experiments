// Generated semantic-recovery benchmark: bitmanip_concat_w16
// Ground-truth expression: {a, b}
module bitmanip_concat_w16(a, b, y);
    input [15:0] a;
    input [15:0] b;
    output [31:0] y;

    assign y = {a, b};
endmodule
