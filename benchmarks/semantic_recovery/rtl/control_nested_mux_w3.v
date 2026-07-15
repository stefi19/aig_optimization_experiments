// Generated semantic-recovery benchmark: control_nested_mux_w3
// Ground-truth expression: sel0 ? (sel1 ? c : b) : a
module control_nested_mux_w3(a, b, c, sel0, sel1, y);
    input [2:0] a;
    input [2:0] b;
    input [2:0] c;
    input sel0;
    input sel1;
    output [2:0] y;

    assign y = sel0 ? (sel1 ? c : b) : a;
endmodule
