# AI Data Analyst with Generative AI and Spark — Student Alert System

*Spanish version: [README.md](README.md)*

An assistant that turns **natural-language questions into executable PySpark code** and answers with a table and an automatic chart. Capstone project for *Cloud Computing*, MSc in Data Science, Universidad Santo Tomás.

**Demo:** [Hugging Face Space](https://huggingface.co/spaces/Adrian0812/analista-datos-ia) · **Team:** Adrian Grateron · Jhonatan Smith Doncel · Jorge Emmanuel Marin

## How it works

```
user question → prompt to the LLM (Z.ai GLM) with the real schema of df
→ generated PySpark code → validation → controlled execution → table + chart
```

- **Data:** Bogotá student alert system, 174,826 records (Jan 2025 – Mar 2026), loaded into a Spark DataFrame with an explicit schema and derived month/quarter variables.
- **Guardrails:** the model may only use `df`, `spark` and `F`; imports, file access, `eval`/`exec`, subprocesses and writes are blocked before execution.
- **App:** Gradio web interface (`app/app.py`), packaged with Docker (Python 3.11 + Java) and deployed on Hugging Face Spaces; the API key is stored as a Space secret.

## Limitations

- Running LLM-generated code with a denylist is acceptable for a prototype, but production would need AST-based allowlisting and a sandboxed process with time and memory limits.
- No systematic accuracy evaluation of the generated code yet; a benchmark of reference questions is the next step.
- The dataset contains sensitive student information and is **not** included in this repository.

**Tech:** PySpark · Gradio · OpenAI SDK (Z.ai GLM) · Docker · Hugging Face Spaces · **License:** CC BY 4.0
