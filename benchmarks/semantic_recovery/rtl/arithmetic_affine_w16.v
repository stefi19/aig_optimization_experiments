// Generated semantic-recovery benchmark: arithmetic_affine_w16
// Ground-truth expression: (a * 3) + 5
module arithmetic_affine_w16(a, y);
    input [15:0] a;
    output [18:0] y;

    assign y = (a * 3) + 5;
endmodule
