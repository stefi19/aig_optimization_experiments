// Generated semantic-recovery benchmark: boolean_parity_w16
// Ground-truth expression: ^a
module boolean_parity_w16(a, y);
    input [15:0] a;
    output y;

    assign y = ^a;
endmodule
