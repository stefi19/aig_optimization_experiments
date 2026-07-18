module sem_controlled_mac(a, b, c, y0, y1);
  input [1:0] a;
  input [1:0] b;
  input [1:0] c;
  output y0;
  output y1;
  assign y0 = ((a * b) + c)[0];
  assign y1 = ((a * b) + c)[1];
endmodule
