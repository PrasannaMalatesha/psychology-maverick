# Config-driven multi-provider model gateway via LiteLLM

All LLM and embedding calls go through a **LiteLLM**-backed registry that maps *logical roles*
(`grader`, `synthesizer`, `judge`, `embedder`) to model strings in configuration. No provider is
hardcoded; any LiteLLM-supported provider (Google, Anthropic, OpenAI, DeepSeek, OpenRouter, local)
is added by config + an API key, with per-role fallback chains.

## Why

- Providers change, go down, and reprice. Role-based routing lets cheap models do cheap work
  (grading, judging) and premium models do synthesis, while fallback chains add resilience.
- OpenRouter as a catch-all means "use any model" is genuinely true without new integration code.
- Swapping or adding a model becomes a config change, not a code change — the whole point of having
  a gateway in the stack.

## Trade-off / consequences

- A thin indirection layer over provider SDKs, and a config surface to maintain.
- **Fallback models must be tested** — switching models can change agent behavior and answer
  quality, so a fallback is not "free" correctness.
- Current reality: only a Google Gemini API key is available (Claude *Pro* is a chat subscription,
  not API access). The design makes adding others later trivial, but the fallback story is only as
  real as the keys present.
