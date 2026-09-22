# OpenCode Setup for Nabd — Installation Guide

## 1. Prerequisites
- Node.js 20+ and npm
- OpenCode installed: `npm i -g opencode-ai`
- An OpenRouter API key with access to DeepSeek models

## 2. Install the configs

From your `nabd/` repo root, run:

```bash
mkdir -p .opencode/agents
cp nabd-coder.agent.md .opencode/agents/nabd-coder.md
cp AGENTS.md AGENTS.md
cp opencode.json opencode.json
```

## 3. Set your API key

```bash
export OPENROUTER_API_KEY="sk-or-..."
# or add it to .env (gitignored)
```

## 4. Start the agent

```bash
opencode
```

Then select the **nabd-coder** agent (or it activates automatically as
`mode: primary`).

## 5. Daily workflow tips

- Keep sessions focused: one module per session (e.g. "build the OCR
  ingestion endpoint") rather than "build everything".
- The agent's bash permissions are pre-configured: tests and safe npm
  commands run automatically; anything else asks you first.
- If DeepSeek gives shallow answers, switch the model for that task:
  `/model openrouter/deepseek/deepseek-r1` (better reasoning for
  architecture decisions), then switch back for implementation.
- Periodically run `opencode` in a fresh session with `/compact` or
  restart — long stale conversations degrade accuracy and cost more.

## 6. Model IDs

Replace `deepseek/deepseek-chat-v3-0324` in both files with the exact
model ID shown in your OpenRouter dashboard if you are using a newer
release (e.g. a V4 endpoint). Get the ID from:
https://openrouter.ai/models?search=deepseek
