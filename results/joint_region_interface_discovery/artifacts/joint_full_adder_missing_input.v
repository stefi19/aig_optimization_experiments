module joint_sem_full_adder_missing_input(a, b, cin, sum, cout);
  input a;
  input b;
  input cin;
  output sum;
  output cout;
  assign sum = ((a ^ b) ^ cin);
  assign cout = (((a & b) | (a & cin)) | (b & cin));
endmodule
