// SPDX-License-Identifier: CC0-1.0
module rtl_affine4(input [3:0] a, input [3:0] b, input cin, output [4:0] y);
  assign y = {1'b0, a} + ({1'b0, b} ^ 5'b00101) + cin;
endmodule
