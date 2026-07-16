// Compact sample of formally verified direct semantic expressions.

module verified_direct_000(a, y);
  input [1:0] a;
  output [4:0] y;
  assign y = (a & 5'd0);
endmodule

module verified_direct_001(a, y);
  input [1:0] a;
  output [4:0] y;
  assign y = (a & 5'd0);
endmodule

module verified_direct_002(a, y);
  input [1:0] a;
  output [4:0] y;
  assign y = (a & 5'd0);
endmodule

module verified_direct_003(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a * 4'd3);
endmodule

module verified_direct_004(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a * 4'd3);
endmodule

module verified_direct_005(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a * 4'd3);
endmodule

module verified_direct_006(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a * 4'd3);
endmodule

module verified_direct_007(a, y);
  input [2:0] a;
  output [4:0] y;
  assign y = (a * 5'd3);
endmodule

module verified_direct_008(a, y);
  input [2:0] a;
  output [4:0] y;
  assign y = (a * 5'd3);
endmodule

module verified_direct_009(a, y);
  input [3:0] a;
  output [5:0] y;
  assign y = (a * 6'd3);
endmodule

module verified_direct_010(a, y);
  input [3:0] a;
  output [5:0] y;
  assign y = (a * 6'd3);
endmodule

module verified_direct_011(a, y);
  input [5:0] a;
  output [7:0] y;
  assign y = (a * 8'd3);
endmodule

module verified_direct_012(a, y);
  input [5:0] a;
  output [7:0] y;
  assign y = (a * 8'd3);
endmodule

module verified_direct_013(a, y);
  input [7:0] a;
  output [9:0] y;
  assign y = (a * 10'd3);
endmodule

module verified_direct_014(a, y);
  input [7:0] a;
  output [9:0] y;
  assign y = (a * 10'd3);
endmodule

module verified_direct_015(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_016(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_017(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_018(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_019(a, b, y);
  input [1:0] a;
  input [1:0] b;
  output [2:0] y;
  assign y = (a & 3'd0);
endmodule

module verified_direct_020(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_021(a, b, y);
  input [1:0] a;
  input [1:0] b;
  output [2:0] y;
  assign y = (a & 3'd0);
endmodule

module verified_direct_022(a, b, y);
  input [1:0] a;
  input [1:0] b;
  output [2:0] y;
  assign y = (a & 3'd0);
endmodule

module verified_direct_023(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_024(a, b, y);
  input [1:0] a;
  input [1:0] b;
  output [2:0] y;
  assign y = (a & 3'd0);
endmodule

module verified_direct_025(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_026(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_027(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_028(b, a, y);
  input [1:0] b;
  input [1:0] a;
  output [2:0] y;
  assign y = (b & 3'd0);
endmodule

module verified_direct_029(a, y);
  input [1:0] a;
  output [1:0] y;
  assign y = (a & 2'd0);
endmodule

module verified_direct_030(a, y);
  input a;
  output [1:0] y;
  assign y = (a | 2'd0);
endmodule

module verified_direct_031(a, y);
  input a;
  output [1:0] y;
  assign y = (a ^ 2'd0);
endmodule

module verified_direct_032(a, y);
  input a;
  output [1:0] y;
  assign y = (a ^ 2'd0);
endmodule

module verified_direct_033(a, y);
  input a;
  output [1:0] y;
  assign y = (a ^ 2'd0);
endmodule

module verified_direct_034(a, y);
  input a;
  output [1:0] y;
  assign y = (a ^ 2'd0);
endmodule

module verified_direct_035(a, y);
  input [1:0] a;
  output [1:0] y;
  assign y = (a & 2'd0);
endmodule

module verified_direct_036(a, y);
  input [1:0] a;
  output [1:0] y;
  assign y = (a & 2'd0);
endmodule

module verified_direct_037(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_038(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_039(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_040(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_041(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_042(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_043(a, y);
  input a;
  output [2:0] y;
  assign y = (a | 3'd0);
endmodule

module verified_direct_044(a, y);
  input a;
  output [2:0] y;
  assign y = (a ^ 3'd0);
endmodule

module verified_direct_045(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a | 4'd0);
endmodule

module verified_direct_046(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a ^ 4'd0);
endmodule

module verified_direct_047(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a | 4'd0);
endmodule

module verified_direct_048(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a ^ 4'd0);
endmodule

module verified_direct_049(a, y);
  input [1:0] a;
  output [3:0] y;
  assign y = (a ^ 4'd0);
endmodule
