# Blind Semantic CEGIS Leakage Audit

- Audited components: 6
- Ground-truth-derived references found: 24
- Inference-time high-risk references in the existing assisted pipeline: 22

The new blind pipeline uses `assert_inference_schema` and writes predictions before evaluation-only joins. Existing assisted/oracle outputs are retained as ablations and are not reported as primary blind evidence.
