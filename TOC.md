# Table of Contents - Interview Prep Notes

Aligned with [SYLLABUS.md](SYLLABUS.md). Each topic has a cheatsheet optimised for revision; many have diagrams + worked examples.

Status: `[ ]` not started * `[~]` in progress * `[x]` done

---

## 01 - CS Fundamentals
- [x] **DSA** -- [cheatsheet (master patterns)](01-CS-Fundamentals/dsa-cheatsheet.md) * [20+ worked examples](01-CS-Fundamentals/dsa-examples.md) * [17 pattern files](01-CS-Fundamentals/dsa-patterns/00-master-index.md)
- [x] **Python nuances** -- [cheatsheet](01-CS-Fundamentals/python-nuances-cheatsheet.md)
- [x] **OOP principles** -- [cheatsheet](01-CS-Fundamentals/oop-cheatsheet.md)
- [x] **SQL** -- [cheatsheet](01-CS-Fundamentals/sql-cheatsheet.md) * [15 worked queries](01-CS-Fundamentals/sql-examples.md)
- [x] **DBMS** -- [cheatsheet](01-CS-Fundamentals/dbms-cheatsheet.md)
- [x] **Operating Systems** -- [cheatsheet](01-CS-Fundamentals/os-cheatsheet.md)
- [x] **Computer Networks** -- [cheatsheet](01-CS-Fundamentals/computer-networks-cheatsheet.md)
- [x] **Data-science libraries** -- [cheatsheet](01-CS-Fundamentals/ds-libs-cheatsheet.md) (numpy / pandas / matplotlib / sklearn / xgboost)

## 02 - ML & Deep Learning
- [x] **ML algorithms** -- [cheatsheet](02-ML-DL/ml-algos-cheatsheet.md)
- [x] **ML evaluation metrics** -- covered inside [ml-algos](02-ML-DL/ml-algos-cheatsheet.md) (confusion matrix, precision/recall/F1, ROC/PR-AUC, bias-variance)
- [x] **DL basics** -- [cheatsheet](02-ML-DL/dl-basics-cheatsheet.md)
- [x] **Gradient descent + optimisers** -- [cheatsheet](02-ML-DL/gradient-descent-cheatsheet.md) * [backprop worked examples](02-ML-DL/backprop-gradient-examples.md)
- [x] **Embeddings** -- [cheatsheet](02-ML-DL/embeddings-nlp-cheatsheet.md) * [runnable examples](02-ML-DL/embeddings-examples.md)
- [x] **CNN / ResNet / U-Net** -- [cheatsheet](02-ML-DL/cnn-resnet-unet-cheatsheet.md)
- [x] **RNN / LSTM / GRU** -- [cheatsheet](02-ML-DL/rnn-lstm-cheatsheet.md)
- [x] **Reinforcement learning** -- [cheatsheet](02-ML-DL/rl-cheatsheet.md)
- [x] **Diffusion** -- [cheatsheet](03-Transformers-LLMs/diffusion-cheatsheet.md)

## 03 - Transformers & LLMs  (priority)
- [x] **Transformers + attention** -- [cheatsheet](03-Transformers-LLMs/transformers-cheatsheet.md) * [deep](03-Transformers-LLMs/transformers-deep.md)
- [x] **BERT family** -- [cheatsheet](03-Transformers-LLMs/bert-gpt-cheatsheet.md)
- [x] **GPT family** -- [cheatsheet](03-Transformers-LLMs/bert-gpt-cheatsheet.md)
- [x] **Tokenizers** -- [cheatsheet](03-Transformers-LLMs/tokenizers-cheatsheet.md) * [worked examples](03-Transformers-LLMs/tokenizers-examples.md)
- [x] **Mixture of Experts (MoE)** -- [cheatsheet](03-Transformers-LLMs/moe-cheatsheet.md)
- [x] **RAG + HNSW** -- [cheatsheet](03-Transformers-LLMs/rag-hnsw-cheatsheet.md) * [deep](03-Transformers-LLMs/rag-hnsw-deep.md)
- [x] **LLM evaluation** -- [cheatsheet](03-Transformers-LLMs/llm-evaluation-cheatsheet.md)
- [x] **KV-cache and inference** -- [cheatsheet](03-Transformers-LLMs/kv-cache-cheatsheet.md)
- [x] **Fine-tuning (LoRA / QLoRA / RLHF / DPO)** -- [cheatsheet](03-Transformers-LLMs/fine-tuning-cheatsheet.md)
- [x] **Prompt engineering** -- [cheatsheet](03-Transformers-LLMs/prompt-engineering-cheatsheet.md)
- [x] **Scaling laws** -- [cheatsheet](03-Transformers-LLMs/scaling-laws-cheatsheet.md)
- [x] **Latest AI models (2026)** -- [cheatsheet](03-Transformers-LLMs/latest-models-cheatsheet.md)

## 04 - AI Agents
- [x] **Agent architecture & design** -- [cheatsheet](04-AI-Agents/architecture-cheatsheet.md)
- [x] **Tools + MCP** -- [cheatsheet](04-AI-Agents/tools-mcp-cheatsheet.md)
- [x] **StateGraph / DAG / LangGraph** -- [cheatsheet](04-AI-Agents/stategraph-cheatsheet.md)
- [x] **Pydantic schemas** -- [cheatsheet](04-AI-Agents/pydantic-cheatsheet.md)
- [x] **Memory + context management** -- [cheatsheet](04-AI-Agents/memory-context-cheatsheet.md)
- [x] **Tool-calling loop** -- inside [architecture](04-AI-Agents/architecture-cheatsheet.md)
- [x] **Rate limiting** -- inside [system design](09-System-Design-Security/system-design-cheatsheet.md) + [agent code examples](04-AI-Agents/agent-code-examples.md)
- [x] **Guardrails + sandbox + HITL** -- [cheatsheet](04-AI-Agents/guardrails-sandbox-hitl-cheatsheet.md)
- [x] **Agent observability** -- inside [architecture](04-AI-Agents/architecture-cheatsheet.md) + [mlops-llmops](07-Deployment/mlops-llmops-cheatsheet.md)
- [x] **Agent code examples** -- [10 runnable recipes](04-AI-Agents/agent-code-examples.md)

## 05 - Backend (Django)
- [x] **Django full** -- [cheatsheet](05-Backend-Django/django-full-cheatsheet.md) * [10 production examples](05-Backend-Django/django-examples.md)
- [x] **Backend observability** -- expanded section inside [django-full](05-Backend-Django/django-full-cheatsheet.md) (logs / metrics / traces / Sentry / OpenTelemetry / request IDs / p95)

## 06 - Frontend (React)
- [x] **React full** -- [cheatsheet](06-Frontend/react-full-cheatsheet.md) * [10 React examples](06-Frontend/react-examples.md)
- [x] **Streaming AI UX** -- expanded section inside [react-full](06-Frontend/react-full-cheatsheet.md) (SSE / WebSocket / cancel / partial markdown / scroll / retry)

## 07 - Deployment, Cloud & MLOps
- [x] **Deployment full** -- [cheatsheet](07-Deployment/deployment-full-cheatsheet.md) * [10 production examples](07-Deployment/deployment-examples.md)
- [x] **MLOps + LLM production operations** -- [cheatsheet](07-Deployment/mlops-llmops-cheatsheet.md)

## 08 - Version Control & Testing
- [x] **Git + testing fundamentals** -- [cheatsheet](08-VCS-Testing/git-testing-cheatsheet.md) * [10 testing examples](08-VCS-Testing/testing-examples.md)
- [x] **AI system testing** -- [cheatsheet](08-VCS-Testing/ai-system-testing-cheatsheet.md)

## 09 - System Design & Security
- [x] **System / API design** -- [cheatsheet](09-System-Design-Security/system-design-cheatsheet.md)
- [x] **HLD / High-Level Design** -- [cheatsheet](09-System-Design-Security/hld-cheatsheet.md)
- [x] **LLD / Low-Level Design** -- [cheatsheet](09-System-Design-Security/lld-cheatsheet.md)
- [x] **Security fundamentals** -- [cheatsheet](09-System-Design-Security/security-cheatsheet.md)
- [x] **LLM security** -- [cheatsheet](09-System-Design-Security/llm-security-cheatsheet.md)

## 10 - Behavioral, Projects & Job Search
- [x] **Job-search playbook** -- [JOB-SEARCH/playbook.md](JOB-SEARCH/playbook.md)
- [x] **Project storytelling templates** -- [behavioral cheatsheet](JOB-SEARCH/behavioral-interview-cheatsheet.md)
- [x] **Behavioral STAR answers** -- [behavioral cheatsheet](JOB-SEARCH/behavioral-interview-cheatsheet.md)
- [x] **Resume bullet alignment** -- [behavioral cheatsheet](JOB-SEARCH/behavioral-interview-cheatsheet.md)
- [x] **Mock interview log** -- [behavioral cheatsheet](JOB-SEARCH/behavioral-interview-cheatsheet.md)

## Community cheatsheets (downloaded PDFs)
- See [cheatsheets/README.md](cheatsheets/README.md) -- ~15 MB of Stanford / Aaron Wang / DS-library cheatsheets.

---

## Build artefacts (Word + PDF)

Every cheatsheet has a `.docx` and `.pdf` rendered to its folder's `out/` subdirectory, plus a combined master under `out_master/INTERVIEW-NOTES-MASTER.{docx,pdf}`. See `memory/dsa-build-pipeline.md` for rebuild commands.
