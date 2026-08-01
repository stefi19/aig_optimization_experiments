// SPDX-License-Identifier: CC0-1.0
module rtl_mux_arith4(input sel, input [3:0] a, input [3:0] b, output [4:0] y);
  wire [4:0] sum = {1'b0, a} + {1'b0, b};
  wire [4:0] diff = {1'b0, a} - {1'b0, b};
  assign y = sel ? sum : diff;
endmodule
