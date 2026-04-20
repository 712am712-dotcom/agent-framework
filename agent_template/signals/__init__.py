# Signal pipeline for this agent.
# Entry: sources.py (what to poll) → adapters/ (how to fetch) → scorer.py (pre-filter)
# Final evaluation happens in prompts/{agent_name}_prompt.txt via the LLM call in main.py
