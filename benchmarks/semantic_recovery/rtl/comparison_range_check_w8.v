// Generated semantic-recovery benchmark: comparison_range_check_w8
// Ground-truth expression: (a >= 2) && (a <= 5)
module comparison_range_check_w8(a, y);
    input [7:0] a;
    output y;

    assign y = (a >= 2) && (a <= 5);
endmodule
