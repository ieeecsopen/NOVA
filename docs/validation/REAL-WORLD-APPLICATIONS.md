# NOVA — Real-World Application Portfolio

**Status:** Production Validation Reference  
**Cross-References:** [BENCHMARK-RESULTS.md](BENCHMARK-RESULTS.md), [ECOSYSTEM-COMPARISON.md](ECOSYSTEM-COMPARISON.md), [VALIDATION-REPORT.md](VALIDATION-REPORT.md)

---

## The 12 Production Reference Applications

| # | Application Domain | Source File | Core Language Invariants Verified |
| :--- | :--- | :--- | :--- |
| **1** | **CLI Tool** | [`01_cli_tool.nova`](../../examples/real-world/01_cli_tool.nova) | Argument parsing, flags, terminal I/O, error exit codes. |
| **2** | **HTTP REST API** | [`02_http_api.nova`](../../examples/real-world/02_http_api.nova) | Route dispatch, JSON request decoding, status codes. |
| **3** | **Database Manager** | [`03_database_app.nova`](../../examples/real-world/03_database_app.nova) | Entity CRUD, linear balance transfer invariants, DbC. |
| **4** | **Reactive Web Frontend** | [`04_web_frontend.nova`](../../examples/real-world/04_web_frontend.nova) | WASM view tree construction, state transitions, zero-DOM overhead. |
| **5** | **Concurrent Service** | [`05_concurrent_service.nova`](../../examples/real-world/05_concurrent_service.nova) | Structured parallel workers, race-free shared memory via Region XOR. |
| **6** | **Distributed Cluster** | [`06_distributed_cluster.nova`](../../examples/real-world/06_distributed_cluster.nova) | Node consensus, saga orchestration, explicit network failure handling. |
| **7** | **WASM Sandbox** | [`07_wasm_application.nova`](../../examples/real-world/07_wasm_application.nova) | WIT component model execution, zero ambient authority. |
| **8** | **AI Agent Governor** | [`08_ai_agent.nova`](../../examples/real-world/08_ai_agent.nova) | Financial budget ceilings ($0.05 max), token counters, safe halting. |
| **9** | **Data Pipeline** | [`09_data_pipeline.nova`](../../examples/real-world/09_data_pipeline.nova) | Streaming record ETL, map/reduce, aggregation invariants. |
| **10**| **Compiler Component** | [`10_compiler_component.nova`](../../examples/real-world/10_compiler_component.nova) | Tokenizer, Pratt expression evaluator, AST transformations. |
| **11**| **Package Resolver** | [`11_package_ecosystem.nova`](../../examples/real-world/11_package_ecosystem.nova) | Supply-chain security, capability auditing in dependencies. |
| **12**| **Full-Stack Platform** | [`12_fullstack_platform.nova`](../../examples/real-world/12_fullstack_platform.nova) | End-to-end multi-tier architecture spanning UI, API, DB, and Auth. |
