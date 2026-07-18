module sem_controlled_bilinear(a, b, c, y0, y1);
  input [1:0] a;
  input [1:0] b;
  input [1:0] c;
  output y0;
  output y1;
  assign y0 = ((((a * b) * 2'd3) + (a * 2'd5)) + ((b * 2'd7) + 2'd1))[0];
  assign y1 = ((((a * b) * 2'd3) + (a * 2'd5)) + ((b * 2'd7) + 2'd1))[1];
endmodule
