from google.adk.agents import LlmAgent

L0 = yaml.safe_dump(_outline(_load_file("index.yaml")["domains"], 0), sort_keys=False)

knowledge_agent = LlmAgent(
    name="knowledge_navigator",
    model="gemini-2.5-flash",
    instruction=f"""
You answer domain questions using a hierarchical knowledge base.

<knowledge_index>
{L0}
</knowledge_index>

Decide how much detail the question needs, then load only that:
1. If the index summaries alone answer it (e.g. "what domains do you cover?") → answer, no tools.
2. Otherwise pick the relevant domain(s). If unsure which, call search_knowledge.
3. Call list_knowledge to see sub-topic summaries. Stop drilling when summaries suffice.
4. Call load_knowledge only on the specific nodes whose full detail you need
   (definitions, formulas, rules, table mappings).
5. Depth guide:
   - "What is X / overview" → summary or L2 definition
   - "How is X calculated / edge cases / exceptions" → full L2 node
   - "Which table/column / write SQL for X" → L3 table mappings
   - Comparisons → load each compared node, nothing else
6. Never answer business definitions from general knowledge. If not found, say so.
7. Already-loaded nodes: {{kb_loaded?}} — don't reload them.
End your answer with the paths you used.
""",
    tools=[list_knowledge, load_knowledge, search_knowledge],
    output_key="knowledge_answer",
)
