// priority_encoder_8.v  –  8-input priority encoder
//
// Inputs : req[7:0]     (8 request lines; higher index = higher priority)
// Outputs: grant[2:0]   (encoded index of highest-priority active request)
//          valid         (1 if any request is active)
//
// To convert to BLIF:
//   yosys -p "read_verilog priority_encoder_8.v; synth -top priority_encoder_8; write_blif priority_encoder_8.blif"

module priority_encoder_8 (
    input  [7:0] req,
    output [2:0] grant,
    output       valid
);
    assign valid = |req;

    assign grant = req[7] ? 3'd7 :
                   req[6] ? 3'd6 :
                   req[5] ? 3'd5 :
                   req[4] ? 3'd4 :
                   req[3] ? 3'd3 :
                   req[2] ? 3'd2 :
                   req[1] ? 3'd1 :
                             3'd0;
endmodule
