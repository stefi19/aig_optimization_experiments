module sem_joint_boolean_region(a, b, c, y0);
  input a;
  input b;
  input c;
  output y0;
  assign y0 = ((a & b) | c);
endmodule
