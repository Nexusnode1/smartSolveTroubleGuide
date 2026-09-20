# Development Instructions

- Treat the supplied official Theme 2 specification PDF and original datasets as the source of truth. Do not invent requirements.
- Preserve original datasets. Do not fabricate deeplinks; use only the supplied deeplink catalog.
- Manual actions must not receive actionable deeplinks, and deeplink targets must match the exact target screen.
- Support query paraphrases and apply the specification's action-sequencing rules.
- Only validated troubleshooting plans may enter or leave the cache. All output must conform to the official schema.
- Use Python `snake_case`, simple maintainable designs, and no unnecessary infrastructure.
- Do not modify unrelated working code. Run relevant tests after meaningful changes and use Git checkpoints.
