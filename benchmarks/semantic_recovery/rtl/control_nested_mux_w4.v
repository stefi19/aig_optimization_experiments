// Generated semantic-recovery benchmark: control_nested_mux_w4
// Ground-truth expression: sel0 ? (sel1 ? c : b) : a
module control_nested_mux_w4(a, b, c, sel0, sel1, y);
    input [3:0] a;
    input [3:0] b;
    input [3:0] c;
    input sel0;
    input sel1;
    output [3:0] y;

    assign y = sel0 ? (sel1 ? c : b) : a;
endmodule
