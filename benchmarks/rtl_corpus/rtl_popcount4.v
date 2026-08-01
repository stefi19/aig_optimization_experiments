// SPDX-License-Identifier: CC0-1.0
module rtl_popcount4(input [3:0] a, output [2:0] y);
  assign y = a[0] + a[1] + a[2] + a[3];
endmodule
