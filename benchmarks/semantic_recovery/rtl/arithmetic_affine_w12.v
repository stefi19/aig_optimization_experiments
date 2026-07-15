// Generated semantic-recovery benchmark: arithmetic_affine_w12
// Ground-truth expression: (a * 3) + 5
module arithmetic_affine_w12(a, y);
    input [11:0] a;
    output [14:0] y;

    assign y = (a * 3) + 5;
endmodule
