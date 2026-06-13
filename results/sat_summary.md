# SAT Refinement Summary

## Overall result

- **Total candidates checked:** 425
- **Verified by ABC:** 0
- **Rejected by ABC:** 425
- **Inconclusive:** 0
- **Verification rate:** 0.0%

## Match category breakdown

Following Carmine's feedback, candidates are now separated into two categories:

- **`exact_anchor`**: the optimized node and original candidate already had identical Boolean simulation signatures before this SAT check. ABC verifying these is a useful sanity check, but it does **not** represent a newly-recovered correspondence — the match was already known.

- **`non_exact_candidate`**: the optimized node and original candidate did **not** have the same simulation signature. ABC verifying one of these is a genuine refinement result — it means the scoring formula identified a real correspondence that exact signature matching missed.

**non_exact_candidate** (425 candidates): verified 0, rejected 425, inconclusive 0 (verification rate 0.0%)

**exact_anchor**: no candidates.

> **Important:** only `non_exact_candidate` verified results should be interpreted as SAT refinement recovering a correspondence that exact matching missed. `exact_anchor` verified results are expected and do not add new information.

## Recovery method breakdown

Each completed check is tagged with the method used to locate the node in the BLIF file:

- **direct** (425): node name found in the BLIF without any fallback
- **fingerprint** (0): node name was missing; recovered via a unique SHA-256 fingerprint match
- **still inconclusive** (0): node could not be resolved (name missing and fingerprint ambiguous/absent, missing BLIF, ABC timeout, etc.)

## Summary by benchmark and optimization

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score | direct_name_count | fingerprint_recovered | still_inconclusive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| generated_multiplier_4 | balance | 0 | 8 | 0 | 8 | 0.00% | 100.00% | 0.00% | 0.9586 | 8 | 0 | 0 |
| generated_multiplier_4 | compress2rs | 0 | 45 | 0 | 45 | 0.00% | 100.00% | 0.00% | 0.9252 | 45 | 0 | 0 |
| generated_multiplier_4 | dc2 | 0 | 51 | 0 | 51 | 0.00% | 100.00% | 0.00% | 0.9224 | 51 | 0 | 0 |
| generated_multiplier_4 | refactor | 0 | 17 | 0 | 17 | 0.00% | 100.00% | 0.00% | 0.9169 | 17 | 0 | 0 |
| generated_multiplier_4 | refactor_z | 0 | 35 | 0 | 35 | 0.00% | 100.00% | 0.00% | 0.9271 | 35 | 0 | 0 |
| generated_multiplier_4 | resub | 0 | 5 | 0 | 5 | 0.00% | 100.00% | 0.00% | 0.9459 | 5 | 0 | 0 |
| generated_multiplier_4 | resyn | 0 | 49 | 0 | 49 | 0.00% | 100.00% | 0.00% | 0.9235 | 49 | 0 | 0 |
| generated_multiplier_4 | resyn2 | 0 | 49 | 0 | 49 | 0.00% | 100.00% | 0.00% | 0.9235 | 49 | 0 | 0 |
| generated_multiplier_4 | resyn2_like | 0 | 49 | 0 | 49 | 0.00% | 100.00% | 0.00% | 0.9235 | 49 | 0 | 0 |
| generated_multiplier_4 | rewrite | 0 | 25 | 0 | 25 | 0.00% | 100.00% | 0.00% | 0.9255 | 25 | 0 | 0 |
| generated_multiplier_4 | rewrite_z | 0 | 47 | 0 | 47 | 0.00% | 100.00% | 0.00% | 0.9250 | 47 | 0 | 0 |
| generated_random_medium | compress2rs | 0 | 3 | 0 | 3 | 0.00% | 100.00% | 0.00% | 0.8838 | 3 | 0 | 0 |
| generated_random_medium | refactor_z | 0 | 6 | 0 | 6 | 0.00% | 100.00% | 0.00% | 0.8708 | 6 | 0 | 0 |
| generated_random_medium | resyn | 0 | 2 | 0 | 2 | 0.00% | 100.00% | 0.00% | 0.8681 | 2 | 0 | 0 |
| generated_random_medium | resyn2 | 0 | 3 | 0 | 3 | 0.00% | 100.00% | 0.00% | 0.8838 | 3 | 0 | 0 |
| generated_random_medium | resyn2_like | 0 | 3 | 0 | 3 | 0.00% | 100.00% | 0.00% | 0.8838 | 3 | 0 | 0 |
| generated_random_medium | rewrite_z | 0 | 3 | 0 | 3 | 0.00% | 100.00% | 0.00% | 0.8708 | 3 | 0 | 0 |
| majority3 | balance | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | compress2rs | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | dc2 | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | refactor_z | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | resyn | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | resyn2 | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | resyn2_like | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| majority3 | rewrite_z | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | balance | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | dc2 | 0 | 3 | 0 | 3 | 0.00% | 100.00% | 0.00% | 0.8750 | 3 | 0 | 0 |
| real_hand_written_full_adder | refactor_z | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | resyn | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | resyn2 | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | resyn2_like | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_full_adder | rewrite_z | 0 | 1 | 0 | 1 | 0.00% | 100.00% | 0.00% | 0.8625 | 1 | 0 | 0 |
| real_hand_written_mux_4to1 | resyn | 0 | 2 | 0 | 2 | 0.00% | 100.00% | 0.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_mux_4to1 | rewrite | 0 | 2 | 0 | 2 | 0.00% | 100.00% | 0.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_mux_4to1 | rewrite_z | 0 | 2 | 0 | 2 | 0.00% | 100.00% | 0.00% | 0.8625 | 2 | 0 | 0 |
| real_hand_written_parity_8 | dc2 | 0 | 2 | 0 | 2 | 0.00% | 100.00% | 0.00% | 0.8625 | 2 | 0 | 0 |

**Global totals:**

| benchmark | optimization | verified | rejected | inconclusive | total | verification_rate | rejection_rate | inconclusive_rate | avg_combined_score | direct_name_count | fingerprint_recovered | still_inconclusive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL | ALL | 0 | 425 | 0 | 425 | 0.00% | 100.00% | 0.00% | 0.9191 | 425 | 0 | 0 |

## Rejected candidates

ABC found 425 candidate(s) to be **not equivalent**:

| benchmark | optimization | optimized_node | original_candidate | combined_score | abc_result |
| --- | --- | --- | --- | --- | --- |
| generated_multiplier_4 | balance | new_n41 | new_n40 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n66 | new_n65 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n74 | new_n73 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n94 | new_n93 | 0.9441 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n102 | new_n101 | 0.9807 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n118 | new_n117 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n123 | new_n122 | 0.9785 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | balance | new_n135 | new_n134 | 0.9441 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n26 | new_n20 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n28 | new_n31 | 0.9161 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n37 | new_n26 | 0.9156 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n39 | new_n45 | 0.9164 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n40 | new_n37 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n44 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | compress2rs | new_n45 | new_n53 | 0.8820 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n46 | new_n55 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n47 | new_n64 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n48 | new_n57 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n49 | new_n55 | 0.8641 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | compress2rs | new_n56 | new_n72 | 0.9242 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n57 | new_n102 | 0.9369 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n58 | new_n103 | 0.8534 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n59 | new_n62 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n60 | new_n65 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n61 | new_n99 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n62 | new_n70 | 0.9135 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n63 | new_n76 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n64 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n65 | new_n82 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n66 | new_n84 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n67 | new_n92 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n68 | new_n86 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n69 | new_n84 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n71 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n75 | new_n101 | 0.9893 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | compress2rs | new_n76 | new_n123 | 0.9785 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n77 | new_n124 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n78 | new_n90 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n79 | new_n93 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n80 | new_n120 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n81 | new_n98 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n82 | new_n104 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n83 | new_n105 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n84 | new_n98 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n85 | new_n108 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n87 | new_n109 | 0.9355 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n90 | new_n106 | 0.8732 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n91 | new_n115 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n92 | new_n122 | 0.9893 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n94 | new_n117 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n95 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | compress2rs | new_n96 | new_n126 | 0.9441 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n26 | new_n20 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n28 | new_n31 | 0.9161 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n40 | new_n45 | 0.9164 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n41 | new_n37 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n42 | new_n49 | 0.8906 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n43 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n44 | new_n48 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n45 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n46 | new_n53 | 0.8820 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n47 | new_n55 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n57 | new_n67 | 0.8563 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n58 | new_n64 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n59 | new_n102 | 0.9412 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n60 | new_n70 | 0.9186 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n61 | new_n76 | 0.9057 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n63 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n64 | new_n70 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n65 | new_n62 | 0.9398 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n66 | new_n100 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n67 | new_n76 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n68 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n69 | new_n82 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n70 | new_n84 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n71 | new_n86 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n72 | new_n92 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n73 | new_n84 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n75 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n79 | new_n78 | 0.8668 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n80 | new_n91 | 0.9441 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n81 | new_n123 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n82 | new_n98 | 0.9207 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n83 | new_n104 | 0.9035 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n84 | new_n101 | 0.9393 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n85 | new_n120 | 0.9957 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n86 | new_n97 | 0.9441 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n87 | new_n98 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n88 | new_n105 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n89 | new_n98 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n90 | new_n108 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n91 | new_n110 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n92 | new_n116 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n95 | new_n106 | 0.8732 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n96 | new_n115 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n97 | new_n124 | 0.9229 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n98 | new_n121 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | dc2 | new_n100 | new_n117 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n101 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n102 | new_n119 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n103 | new_n133 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | dc2 | new_n105 | new_n119 | 0.8754 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n27 | new_n28 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | refactor | new_n28 | new_n27 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n43 | new_n45 | 0.9414 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n44 | new_n43 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n50 | new_n53 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n51 | new_n55 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n69 | new_n70 | 0.9436 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n70 | new_n76 | 0.9307 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n76 | new_n82 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n77 | new_n84 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n82 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n94 | new_n98 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n95 | new_n104 | 0.9285 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n101 | new_n110 | 0.8920 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n102 | new_n112 | 0.8920 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n116 | new_n119 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor | new_n117 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n27 | new_n28 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n28 | new_n27 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | refactor_z | new_n41 | new_n26 | 0.9156 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n43 | new_n45 | 0.9414 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n44 | new_n43 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | refactor_z | new_n50 | new_n53 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n51 | new_n55 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n62 | new_n49 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n63 | new_n64 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n65 | new_n70 | 0.9436 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n66 | new_n76 | 0.9307 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n69 | new_n75 | 0.9033 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n70 | new_n72 | 0.9242 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n76 | new_n82 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n77 | new_n84 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n82 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n87 | new_n78 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n88 | new_n97 | 0.9157 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n90 | new_n98 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n91 | new_n104 | 0.9285 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n92 | new_n67 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n94 | new_n101 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n95 | new_n100 | 0.9350 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n101 | new_n110 | 0.8920 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n102 | new_n112 | 0.8920 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n109 | new_n106 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n110 | new_n125 | 0.9204 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n111 | new_n95 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n113 | new_n122 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n114 | new_n121 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n116 | new_n119 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n117 | new_n125 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n121 | new_n124 | 0.8797 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n122 | new_n105 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | refactor_z | new_n123 | new_n119 | 0.9957 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resub | new_n69 | new_n72 | 0.9207 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resub | new_n87 | new_n97 | 0.9118 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resub | new_n93 | new_n100 | 0.9207 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resub | new_n111 | new_n120 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resub | new_n112 | new_n135 | 0.9893 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n26 | new_n20 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n28 | new_n31 | 0.9161 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n41 | new_n45 | 0.9164 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n42 | new_n37 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n43 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n44 | new_n49 | 0.8906 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n45 | new_n48 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n46 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n47 | new_n53 | 0.8820 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn | new_n48 | new_n55 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n58 | new_n67 | 0.8563 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n59 | new_n64 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn | new_n61 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n62 | new_n102 | 0.9369 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n63 | new_n103 | 0.8534 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn | new_n64 | new_n62 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n65 | new_n69 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n66 | new_n68 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n67 | new_n70 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n68 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n69 | new_n82 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n70 | new_n84 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n71 | new_n92 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n72 | new_n86 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n73 | new_n84 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n75 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n79 | new_n70 | 0.8818 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n80 | new_n100 | 0.9850 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n81 | new_n123 | 0.9785 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n82 | new_n124 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n83 | new_n90 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n84 | new_n92 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n86 | new_n98 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n87 | new_n123 | 0.9479 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n88 | new_n120 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n89 | new_n104 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n90 | new_n105 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n91 | new_n98 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n92 | new_n108 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n94 | new_n109 | 0.9355 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n97 | new_n122 | 0.9393 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n98 | new_n106 | 0.8732 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n99 | new_n115 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n101 | new_n117 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n102 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n103 | new_n133 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n104 | new_n119 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn | new_n106 | new_n119 | 0.8754 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n26 | new_n20 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2 | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n28 | new_n31 | 0.9161 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n40 | new_n45 | 0.9164 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n41 | new_n37 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2 | new_n42 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2 | new_n43 | new_n49 | 0.8906 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n44 | new_n48 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2 | new_n45 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n46 | new_n53 | 0.8820 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n47 | new_n55 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2 | new_n57 | new_n67 | 0.8563 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n58 | new_n64 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n60 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n61 | new_n102 | 0.9369 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n62 | new_n103 | 0.8534 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n63 | new_n62 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n64 | new_n69 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n65 | new_n68 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n66 | new_n70 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n67 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n68 | new_n82 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n69 | new_n84 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n70 | new_n92 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n71 | new_n86 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n72 | new_n84 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n74 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n78 | new_n70 | 0.8818 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n79 | new_n100 | 0.9850 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n80 | new_n123 | 0.9785 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n81 | new_n124 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n82 | new_n90 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n83 | new_n92 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n85 | new_n98 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n86 | new_n123 | 0.9479 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n87 | new_n120 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n88 | new_n104 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n89 | new_n105 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n90 | new_n98 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n91 | new_n108 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n93 | new_n109 | 0.9355 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n96 | new_n122 | 0.9393 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n97 | new_n106 | 0.8732 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n98 | new_n115 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n100 | new_n117 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n101 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n102 | new_n133 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n103 | new_n119 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2 | new_n105 | new_n119 | 0.8754 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n26 | new_n20 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n28 | new_n31 | 0.9161 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2_like | new_n40 | new_n45 | 0.9164 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n41 | new_n37 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n42 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n43 | new_n49 | 0.8906 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n44 | new_n48 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n45 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n46 | new_n53 | 0.8820 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n47 | new_n55 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| generated_multiplier_4 | resyn2_like | new_n57 | new_n67 | 0.8563 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n58 | new_n64 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n60 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n61 | new_n102 | 0.9369 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n62 | new_n103 | 0.8534 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n63 | new_n62 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n64 | new_n69 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n65 | new_n68 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n66 | new_n70 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n67 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n68 | new_n82 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n69 | new_n84 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n70 | new_n92 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n71 | new_n86 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n72 | new_n84 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n74 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n78 | new_n70 | 0.8818 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n79 | new_n100 | 0.9850 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n80 | new_n123 | 0.9785 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n81 | new_n124 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n82 | new_n90 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n83 | new_n92 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n85 | new_n98 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n86 | new_n123 | 0.9479 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n87 | new_n120 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n88 | new_n104 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n89 | new_n105 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n90 | new_n98 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n91 | new_n108 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n93 | new_n109 | 0.9355 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n96 | new_n122 | 0.9393 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n97 | new_n106 | 0.8732 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n98 | new_n115 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n100 | new_n117 | 0.9699 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n101 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n102 | new_n133 | 0.9828 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n103 | new_n119 | 0.8684 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | resyn2_like | new_n105 | new_n119 | 0.8754 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n42 | new_n45 | 0.9414 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n43 | new_n43 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n49 | new_n53 | 0.9070 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n50 | new_n55 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n59 | new_n64 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n62 | new_n70 | 0.9436 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n63 | new_n76 | 0.9307 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n64 | new_n73 | 0.8797 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n65 | new_n72 | 0.9076 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n71 | new_n82 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n72 | new_n84 | 0.8941 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n77 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n80 | new_n92 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n83 | new_n98 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n84 | new_n104 | 0.9285 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n85 | new_n101 | 0.9678 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n86 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n92 | new_n110 | 0.8920 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n93 | new_n112 | 0.8920 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n98 | new_n116 | 0.9328 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n100 | new_n122 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n101 | new_n105 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n103 | new_n119 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n104 | new_n125 | 0.9371 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite | new_n108 | new_n133 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n26 | new_n20 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n27 | new_n27 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n28 | new_n31 | 0.9161 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n40 | new_n40 | 0.9656 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n43 | new_n45 | 0.9164 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n44 | new_n37 | 0.9484 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n45 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n46 | new_n49 | 0.8906 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n47 | new_n48 | 0.8984 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n48 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n49 | new_n53 | 0.8820 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n50 | new_n55 | 0.8734 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n61 | new_n47 | 0.9570 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n64 | new_n102 | 0.9412 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n65 | new_n70 | 0.9186 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n66 | new_n76 | 0.9057 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n68 | new_n72 | 0.9742 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n69 | new_n100 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n70 | new_n70 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n71 | new_n76 | 0.9264 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n72 | new_n77 | 0.9549 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n73 | new_n82 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n74 | new_n84 | 0.8691 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n79 | new_n86 | 0.8727 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n84 | new_n77 | 0.9291 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n86 | new_n78 | 0.9313 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n87 | new_n123 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n88 | new_n98 | 0.9207 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n89 | new_n104 | 0.9035 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n90 | new_n103 | 0.9035 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n91 | new_n100 | 0.9850 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n92 | new_n121 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n93 | new_n98 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n94 | new_n104 | 0.9457 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n95 | new_n105 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n96 | new_n98 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n97 | new_n108 | 0.8705 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n98 | new_n109 | 0.9355 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n101 | new_n124 | 0.9229 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n102 | new_n121 | 0.9871 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n104 | new_n104 | 0.9527 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n107 | new_n106 | 0.9355 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n108 | new_n115 | 0.9420 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n109 | new_n119 | 0.8603 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n110 | new_n130 | 0.8513 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n111 | new_n126 | 0.9414 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_multiplier_4 | rewrite_z | new_n112 | new_n119 | 0.8668 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | compress2rs | new_n25 | new_n28 | 0.8800 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | compress2rs | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | compress2rs | new_n28 | new_n29 | 0.9151 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | refactor_z | new_n26 | new_n28 | 0.8800 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | refactor_z | new_n27 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | refactor_z | new_n28 | new_n27 | 0.8761 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | refactor_z | new_n34 | new_n36 | 0.8814 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | refactor_z | new_n35 | new_n34 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | refactor_z | new_n36 | new_n35 | 0.8748 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn | new_n23 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn | new_n27 | new_n28 | 0.8800 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2 | new_n25 | new_n28 | 0.8800 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2 | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2 | new_n28 | new_n29 | 0.9151 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2_like | new_n25 | new_n28 | 0.8800 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2_like | new_n26 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | resyn2_like | new_n28 | new_n29 | 0.9151 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | rewrite_z | new_n26 | new_n28 | 0.8800 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | rewrite_z | new_n27 | new_n26 | 0.8562 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| generated_random_medium | rewrite_z | new_n28 | new_n27 | 0.8761 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | balance | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | compress2rs | new_n7 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | dc2 | new_n7 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | refactor_z | new_n7 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | resyn | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| majority3 | resyn2 | new_n7 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | resyn2_like | new_n7 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| majority3 | rewrite_z | new_n8 | new_n8 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | balance | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | dc2 | new_n9 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | dc2 | new_n11 | new_n10 | 0.8813 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | dc2 | new_n12 | new_n9 | 0.8813 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | refactor_z | new_n14 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | resyn | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | resyn2 | new_n14 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_full_adder | resyn2_like | new_n14 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_full_adder | rewrite_z | new_n15 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_mux_4to1 | resyn | new_n10 | new_n15 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_mux_4to1 | resyn | new_n14 | new_n11 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |
| real_hand_written_mux_4to1 | rewrite | new_n9 | new_n13 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_mux_4to1 | rewrite | new_n13 | new_n9 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_mux_4to1 | rewrite_z | new_n9 | new_n13 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_mux_4to1 | rewrite_z | new_n13 | new_n9 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_parity_8 | dc2 | new_n28 | new_n28 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.01 sec |
| real_hand_written_parity_8 | dc2 | new_n29 | new_n28 | 0.8625 | Networks are NOT EQUIVALENT.  Time =     0.00 sec |

A rejected candidate means the simulation ranking assigned a high score to a pair that ABC proved are not logically equivalent. This shows why a formal check is necessary: simulation similarity alone is not a proof of equivalence.

## Inconclusive candidates

No inconclusive candidates.

## Main interpretation

The SAT refinement step is currently most useful as a false-positive filter. ABC rejected every checked high-confidence non-exact candidate, so these rows cannot be claimed as recovered internal correspondences. This is still useful evidence: high simulation/support/depth scores are not enough to imply functional equivalence, and formal checking can separate structural similarity from true node equivalence.
There were no inconclusive candidates in this run, so the SAT results are usable as formal verdicts for the selected candidate set.
