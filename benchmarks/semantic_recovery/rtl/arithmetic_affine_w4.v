// Generated semantic-recovery benchmark: arithmetic_affine_w4
// Ground-truth expression: (a * 3) + 5
module arithmetic_affine_w4(a, y);
    input [3:0] a;
    output [6:0] y;

    assign y = (a * 3) + 5;
endmodule
