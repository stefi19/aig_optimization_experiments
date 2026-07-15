// Generated semantic-recovery benchmark: comparison_range_check_w6
// Ground-truth expression: (a >= 2) && (a <= 5)
module comparison_range_check_w6(a, y);
    input [5:0] a;
    output y;

    assign y = (a >= 2) && (a <= 5);
endmodule
