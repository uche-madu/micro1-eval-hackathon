# Artifact state: 20 turns

You are maintaining a JSON configuration. The initial config is in `/data/initial.json`. You will receive 20 short change requests.

- The conversation is the current state. Later requests supersede earlier ones.
- After every request, output the **complete updated config as JSON**. Do not output a diff, a fragment, or commentary.
- Keep every field. Do not drop fields.
- When the request says "Return the current/final config", return the complete JSON.
- Use only the values in the conversation. Do not use outside knowledge.
