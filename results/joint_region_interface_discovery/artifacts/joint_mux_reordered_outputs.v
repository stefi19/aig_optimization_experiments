module joint_sem_mux(sel, a, b, y0, y1);
  input sel;
  input [1:0] a;
  input [1:0] b;
  output y0;
  output y1;
  assign y0 = (sel ? a : b)[0];
  assign y1 = (sel ? a : b)[1];
endmodule
