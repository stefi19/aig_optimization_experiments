// Tiny controlled source-mapping example.
//
// Expected source-level signals for metadata probes:
//   mix        - combinational expression: a ^ b
//   gated      - combinational expression: mix & enable
//   next_state - combinational expression: gated | c
//   state_q    - registered output state

module simple_pipeline (
    input wire clk,
    input wire enable,
    input wire a,
    input wire b,
    input wire c,
    output wire y
);
    wire mix;
    wire gated;
    wire next_state;
    reg state_q;

    assign mix = a ^ b;
    assign gated = mix & enable;
    assign next_state = gated | c;

    always @(posedge clk) begin
        state_q <= next_state;
    end

    assign y = state_q;
endmodule
