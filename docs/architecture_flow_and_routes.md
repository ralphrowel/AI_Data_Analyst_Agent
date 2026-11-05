# Visiq Architecture Flow & API Route Topology

> **Comprehensive Architectural Blueprint & Routing Specification**  
> *Documenting the unified system architecture of Visiq after integrating the deterministic Data Quality & Cleaning Suite with the Quality-Aware Autonomous AI Data Analyst Agent.*

---

## 1. Executive Overview & System Topology

Visiq unifies two foundational systems into a single, cohesive, multi-tenant enterprise data platform:

1. **Deterministic Data Quality & Cleaning Engine:** A rule-based, mathematically verifiable pipeline built on Pandas and NumPy that evaluates tabular datasets across six core quality dimensions, generates remediation plans, and executes immutable transformations while isolating irrecoverable records into dedicated quarantine tables.
2. **Quality-Aware Autonomous AI Data Analyst Agent:** An intelligent analytical coordinator powered by high-throughput LLMs (Groq `gpt-oss-120b` and Google Gemini `gemini-2.5-flash` with dual-key rotation) that generates structured JSON tool execution plans against Pandas DataFrames—completely avoiding arbitrary code `eval()` and deterministically attaching dataset quality badges outside the LLM context to prevent prompt contamination.

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Client Layer (React 19 + Tailwind + Vite)"]
        UI_HOME["Landing & Workspace (/)]"]
        UI_CHAT["Chat & Query Panel (MessageBubble, InputBar)"]
        UI_GRID["Spreadsheet Panel (Ag-Grid Style, Pagination, Inline Edits)"]
        UI_DQ["Quality Health Panel (Health Badge, Issues Drawer, Plan Wizard)"]
        UI_DASH["Live Dashboard (Pinned Insight Widgets, Auto-Recompute)"]
    end

    subgraph SecurityGateway["FastAPI Gateway & Security Boundary (main.py)"]
        CORS["CORSMiddleware (Vercel & Localhost Allowed)"]
        REQ_BOUND["RequestBoundary (Size Limit: 5 MB / HTTP 413, UUID Request-ID)"]
        AUTH_GUARD["Supabase Auth / Demo JWT Authenticator (get_current_user)"]
        RATE_LIMIT["In-Memory Sliding Window RateLimiter (Per-Route Policies)"]
        QUOTA_GUARD["User Quota Manager (Daily Token & Query Limits)"]
    end

    subgraph APIRoutes["FastAPI Application Routers"]
        R_CORE["Core Router (backend/app/api/routes.py)"]
        R_DQ["Quality Router (backend/app/api/quality_routes.py)"]
    end

    subgraph BusinessEngines["Business Logic & Service Layer"]
        SVC_DQ["DataQualityService (service.py)"]
        DM["DatasetManager (dataset_manager.py)"]
        COORD["AgentCoordinator (coordinator.py)"]
        WIDGET["WidgetEngine (widget_engine.py)"]
        SESS["SessionStore (session_store.py)"]
    end

    subgraph ExecutionEngines["Execution & Intelligence Engines"]
        ENG_PROF["DataProfiler (Statistical & Semantic Profiling)"]
        ENG_CHECK["DataQualityEngine (Integrity Rules & Outlier Detection)"]
        ENG_SCORE["DataQualityScorer (6-Dimension Scoring & Grades)"]
        ENG_CLEAN["DataCleaningEngine (10-Stage Deterministic Pipeline)"]
        ENG_ROUTER["QueryRouter (LLM Intent Classification: Structured / RAG / Hybrid)"]
        ENG_TOOLS["ToolRegistry (Pandas Structured Tools: Filter, Agg, Group, Sort)"]
        ENG_RAG["RAGRetriever (Knowledge Base Vector Embeddings)"]
        ENG_CHART["ChartTool (Matplotlib In-Memory SVG / PNG Spec Generator)"]
    end

    subgraph StorageLayer["Multi-Tenant Persistence Layer"]
        FILE_STORE["FileStore (Supabase Storage Bucket / Local filesystem uploads/)"]
        DB_STORE["Database Storage (Supabase PostgreSQL RLS / Local SQLite visiq.db)"]
        LLM_EXT["External LLM Providers (Groq Cloud API / Gemini API Dual Rotation)"]
    end

    %% Client to Gateway
    ClientLayer --> CORS
    CORS --> REQ_BOUND
    REQ_BOUND --> AUTH_GUARD
    AUTH_GUARD --> RATE_LIMIT
    RATE_LIMIT --> QUOTA_GUARD

    %% Gateway to Routers
    QUOTA_GUARD --> R_CORE
    QUOTA_GUARD --> R_DQ

    %% Routers to Services
    R_CORE --> DM
    R_CORE --> COORD
    R_CORE --> WIDGET
    R_CORE --> SESS
    R_DQ --> SVC_DQ

    %% Services to Engines
    SVC_DQ --> ENG_PROF
    SVC_DQ --> ENG_CHECK
    SVC_DQ --> ENG_SCORE
    SVC_DQ --> ENG_CLEAN

    COORD --> ENG_ROUTER
    COORD --> ENG_TOOLS
    COORD --> ENG_RAG
    COORD --> ENG_CHART
    COORD -.->|Deterministic Quality Badge| SVC_DQ

    WIDGET --> ENG_TOOLS
    WIDGET --> ENG_CHART

    %% Services to Storage
    DM --> FILE_STORE
    SVC_DQ --> FILE_STORE
    SVC_DQ --> DB_STORE
    SESS --> DB_STORE
    ENG_ROUTER --> LLM_EXT
    COORD --> LLM_EXT
```

---

## 2. End-to-End Architectural Flowcharts

### 2.1 Data Ingestion, Profiling & Health Assessment Flow

When a user uploads a new dataset or requests a quality health check, the system executes an automated profiling and scoring pass. Assessment results are indexed by dataset content hash (SHA-256 fingerprint), enabling instant cached retrieval on subsequent requests without recomputing.

```mermaid
flowchart TD
    START(["User Uploads File (.csv, .md, .txt)"]) --> HTTP_POST["POST /api/upload"]
    
    subgraph IngestionGuard["1. Ingestion Guardrails"]
        HTTP_POST --> SIZE_CHK{"Content-Length <= 5 MB?"}
        SIZE_CHK -- No --> E413["HTTP 413: Upload exceeds size limit"]
        SIZE_CHK -- Yes --> TYPE_CHK{"File Extension?"}
        TYPE_CHK -- ".md / .txt" --> RAG_SAVE["Save to Knowledge Store -> Auto-trigger RAG Indexing"]
        TYPE_CHK -- ".csv" --> CSV_PARSE{"Pandas parses CSV?"}
        CSV_PARSE -- No --> E422["HTTP 422: Invalid CSV dataset"]
        CSV_PARSE -- Yes --> FS_SAVE["FileStore.save(owner_id, filename, csv_bytes)"]
    end

    subgraph ProfilingPipeline["2. Profiling & Fingerprinting Engine"]
        FS_SAVE --> FP["Compute SHA-256 Fingerprint of Raw Bytes"]
        FP --> GET_QUAL["GET /api/datasets/{name}/quality"]
        GET_QUAL --> CHK_CACHE{"Cached report in app_records matching hash?"}
        CHK_CACHE -- Yes & !force_refresh --> RET_CACHE["Return Cached QualityAssessmentResult"]
        CHK_CACHE -- No / force_refresh --> PROF["DataProfiler.profile(df)"]
        PROF --> DQE["DataQualityEngine.analyze(df)"]
        DQE --> DQS["DataQualityScorer.score(df, report)"]
    end

    subgraph ScoringAggregation["3. Dimension Scoring & Suggestion"]
        DQS --> DIMS["Evaluate Dimensions: Completeness, Uniqueness, Validity, Consistency, Accuracy, Integrity"]
        DIMS --> OVERALL["Calculate Overall Score (0-100) & Grade (A, B, C, D, F)"]
        OVERALL --> PLAN_GEN["generate_suggested_plan(report, df)"]
        PLAN_GEN --> CACHE_PUT["storage.put('dq_reports', owner, dataset, assessment)"]
        CACHE_PUT --> RESP_QUAL["HTTP 200: QualityAssessmentResult JSON"]
    end

    RESP_QUAL --> UI_BADGE["UI Renders Grade Pill, Score Ring, & Issue Inventory"]
```

---

### 2.2 Deterministic Cleaning, Quarantine & Lineage Flow

Cleaning in Visiq is **stateless, deterministic, and non-destructive**. The original dataset is never overwritten. Instead, the engine creates an immutable child version (`{stem}__clean_v{N}.csv`), isolates unrecoverable records into `{stem}__quarantine_v{N}.csv`, and registers full lineage relationships in the database.

```mermaid
flowchart TD
    USER_ACTION(["User inspects issues & configures cleaning plan"]) --> DRY_RUN{"Action Type"}

    subgraph PreviewPhase["1. Stateless Dry-Run Preview"]
        DRY_RUN -- Preview --> POST_PREV["POST /api/datasets/{name}/clean/preview"]
        POST_PREV --> CLEAN_MEM["DataCleaningEngine.clean(raw_df, **plan) in memory"]
        CLEAN_MEM --> COMPARE["DataQualityScorer.compare(raw_df, cleaned_df)"]
        COMPARE --> PREV_RESP["HTTP 200: Before/After Stats, Diff Counts, Score Delta"]
        PREV_RESP --> UI_PREV["UI displays preview diff modal without saving"]
    end

    subgraph ApplyPhase["2. Execution & Snapshot Generation"]
        DRY_RUN -- Apply Plan --> POST_APPLY["POST /api/datasets/{name}/clean"]
        POST_APPLY --> PIPELINE["Execute 10-Stage Cleaning Pipeline"]
        
        subgraph PipelineStages["Cleaning Pipeline Stages"]
            PIPELINE --> S1["1. Normalize Column Names & Headers"]
            S1 --> S2["2. String Whitespace Trimming"]
            S2 --> S3["3. Categorical Casing & Alias Standardization"]
            S3 --> S4["4. Date Normalization to ISO-8601 (YYYY-MM-DD)"]
            S4 --> S5["5. Currency & Numeric Stripping (₱, $, commas, suffixes)"]
            S5 --> S6["6. Outlier & Corrupt Record Quarantine Router"]
            S6 --> S7["7. Deduplication (Exact / Key Subset)"]
            S7 --> S8["8. Missing Value Imputation (mean, median, mode, drop)"]
            S8 --> S9["9. Strict Type Coercion"]
            S9 --> S10["10. Formula-Injection CSV Sanitization"]
        end

        S10 --> SPLIT{"Were fatal records quarantined?"}
        SPLIT -- Yes --> QUAR_DF["quarantine_df -> {stem}__quarantine_v{N}.csv"]
        SPLIT -- No / Also --> CLEAN_DF["cleaned_df -> {stem}__clean_v{N}.csv"]
    end

    subgraph LineagePersist["3. Lineage & Session Attachment"]
        CLEAN_DF --> SAVE_CLEAN["FileStore.save(owner, clean_snapshot)"]
        QUAR_DF --> SAVE_QUAR["FileStore.save(owner, quarantine_snapshot)"]
        SAVE_CLEAN --> JOB_REC["Create CleaningJob Record (Score Before -> After)"]
        SAVE_QUAR --> JOB_REC
        JOB_REC --> LIN_REC["Update DatasetLineage (Parent original <-> Child clean_vN)"]
        LIN_REC --> DB_SAVE["storage.put('dataset_lineage' & 'dq_jobs')"]
        DB_SAVE --> AUTO_SWITCH["PATCH /api/sessions/{session_id}/dataset"]
        AUTO_SWITCH --> READY(["Active Chat Session Re-pointed to Clean Dataset"])
    end
```

---

### 2.3 Quality-Aware Analytics Agent Query Execution Flow

When a user submits an analytical question via `POST /api/ask`, the coordinator processes the request through intent routing, structured tool execution, and dynamic chart extraction. To preserve mathematical integrity, **the quality badge is calculated deterministically outside the LLM context**, preventing model hallucination or prompt contamination.

```mermaid
flowchart TD
    USER_QUERY(["User Question (e.g. 'What is total revenue by region?')"]) --> ASK_ROUTE["POST /api/ask"]

    subgraph PreExecutionGuards["1. Security, Quota & Session Verification"]
        ASK_ROUTE --> CHK_QUOTA{"Daily Query & Token Quota Remaining?"}
        CHK_QUOTA -- Exceeded --> E429["HTTP 429: Daily token/query limit reached"]
        CHK_QUOTA -- OK --> VERIFY_SESS["Resolve Session & Active Dataset (raw vs clean_vN)"]
        VERIFY_SESS --> RECORD_TURN["SessionStore.add_turn('user', question)"]
    end

    subgraph AgentOrchestration["2. Agent Intent Routing & Tool Calling"]
        RECORD_TURN --> ROUTER["QueryRouter.route(question)"]
        ROUTER --> ROUTE_TYPE{"Classified Route"}
        
        ROUTE_TYPE -- "rag" --> RAG_EXEC["RAGRetriever: Semantic search across indexed docs"]
        ROUTE_TYPE -- "structured" --> LLM_TOOL_PLAN["LLM Call (Groq / Gemini): Select tool & parameters"]
        ROUTE_TYPE -- "hybrid" --> HYBRID["Execute Structured Tool + RAG Search"]

        LLM_TOOL_PLAN --> TOOL_JSON["Extract Structured JSON Tool Call (NO eval())"]
        TOOL_JSON --> TOOL_REG{"ToolRegistry.execute(tool, active_df, params)"}
        
        subgraph ToolSuite["Structured Pandas Tools"]
            TOOL_REG --> T_SCHEMA["get_dataset_schema"]
            TOOL_REG --> T_FILTER["filter_rows (eq, contains, gt, lt)"]
            TOOL_REG --> T_AGG["aggregate_data (sum, mean, count, min, max)"]
            TOOL_REG --> T_GROUP["group_data (group_by + agg)"]
            TOOL_REG --> T_SORT["sort_data (top N, order)"]
            TOOL_REG --> T_DQ["get_quality_report (quality stats)"]
        end
    end

    subgraph ResponseSynthesis["3. Chart Synthesis & Quality Badging"]
        TOOL_REG --> EXEC_RES["Raw Pandas Tool Execution Result"]
        EXEC_RES --> CHART_GEN["ChartTool.generate_chart & extract_chart_spec"]
        EXEC_RES --> SUMM["LLM Natural Language Summarizer Prompt"]
        CHART_GEN --> SPEC_OUT["Matplotlib In-Memory SVG + Base64 PNG + Spec JSON"]
        SUMM --> TEXT_OUT["Plain-English Insight Summary"]

        TEXT_OUT --> DET_BADGE["_resolve_quality_badge(dataset_name, user_id)"]
        DET_BADGE --> BADGE_META["Deterministic Metadata: Score, Grade, Trustworthy Flag, Warning"]
    end

    subgraph FinalDispatch["4. Atomic Storage & Client Dispatch"]
        BADGE_META --> ATOMIC_QUOTA["default_quota_manager.record_query(user_id)"]
        ATOMIC_QUOTA --> SESS_TURN["SessionStore.add_turn('assistant', summary, meta)"]
        SESS_TURN --> FINAL_RESP["HTTP 200: AnalysisResponse JSON"]
    end

    FINAL_RESP --> UI_RENDER(["UI Renders Answer Text + Interactive Chart + Quality Badge Pill"])
```

---

### 2.4 Live Dashboard Widgets & Zero-AI Auto-Recompute Flow

Widgets pinned to a session dashboard execute dynamic analytical operations against the session's underlying dataset. If a dataset is edited in the spreadsheet or switched from raw to clean, **widgets can be recalculated with zero LLM API consumption**.

```mermaid
flowchart LR
    subgraph WidgetCreation["Widget Creation"]
        PIN_REQ["POST /api/sessions/{id}/widgets/pin"] --> W_PIN["WidgetEngine.create_widget_from_chat()"]
        PROMPT_REQ["POST /api/sessions/{id}/widgets"] --> W_PROMPT["WidgetEngine.create_widget_from_prompt()"]
        W_PIN --> STORE_W["Persist in SessionStore.widgets"]
        W_PROMPT --> STORE_W
    end

    subgraph DatasetMutation["Dataset Mutation Trigger"]
        EDIT["POST /api/datasets/{name}/update (Cell Edit)"] --> MUTATE["Session DataFrame Updated"]
        ADD_ROW["POST /api/datasets/{name}/rows/add"] --> MUTATE
        SWITCH["PATCH /api/sessions/{id}/dataset (Raw -> Clean v1)"] --> MUTATE
    end

    subgraph ZeroCostRecompute["0-AI Recomputation Engine"]
        MUTATE --> RECOMP_REQ["POST /api/sessions/{id}/widgets/recompute"]
        RECOMP_REQ --> ITER["Iterate through all pinned widgets"]
        ITER --> RE_EXEC["Execute cached operation spec against new df"]
        RE_EXEC --> RE_CHART["Regenerate Matplotlib SVG/Base64 Charts"]
        RE_CHART --> ZERO_CALL["0 LLM Calls Consumed / 0 Quota Deducted"]
        ZERO_CALL --> RESP_W["HTTP 200: Updated Widgets Array"]
    end
```

---

## 3. Unified API Route Directory & Specifications

The table below catalogs every endpoint across the application, detailing router origin, security policies, payload contracts, service dependencies, and roles in the integrated system.

| HTTP Method | Route Path | Router Module | Auth / Rate Limit Policy | Request Body / Query Params | Primary Service Invoked | Response Output | Architectural Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | `routes.py` | Public | None | None | `{"status": "...", "architecture": "modular"}` | Root service health check and gateway availability probe. |
| `GET` | `/api/auth/me` | `routes.py` | `get_current_user` | None | `default_quota_manager` | User profile object + daily token/query quota allowance. | Hydrates client authentication state and user header pill. |
| `GET` | `/api/user/quota` | `routes.py` | `get_current_user` | None | `default_quota_manager` | `UserQuotaResponse` (used, limit, remaining). | Real-time rate and quota usage tracking in the client header. |
| `POST` | `/api/auth/login` | `routes.py` | Public | `LoginRequest` (`username`, `password`) | Password verification | JWT token string + User object | Administrator and internal demo credentials login. |
| `GET` | `/api/datasets` | `routes.py` | `get_current_user` | None | `default_dataset_manager` | `List[DatasetInfo]` | Lists all accessible global datasets and private user uploads. |
| `POST` | `/api/upload` | `routes.py` | `get_current_user`, RateLimit (5/min) | `UploadDatasetRequest` (`filename`, `content`) | `FileStore`, `storage.transaction`, `DatasetManager` | `UploadResponse` (`name`, `rows`, `cols`, `size_bytes`, `type`) | Secure ingestion of CSV datasets or RAG knowledge files (`.md`, `.txt`). |
| `GET` | `/api/datasets/{name}/rows` | `routes.py` | `get_current_user` | `page`, `page_size`, `search`, `sort_by`, `sort_order` | `DatasetManager.get_rows_paginated()` | Paginated row array, column definitions, total row counts. | Powers interactive spreadsheet view with server-side pagination & filtering. |
| `POST` | `/api/datasets/{name}/update` | `routes.py` | `get_current_user` | `UpdateDatasetRequest` (row, col, value) | `DatasetManager.update_cells()` | Update confirmation + synced metadata | Allows manual inline cell editing in spreadsheet grid. |
| `POST` | `/api/datasets/{name}/rows/add` | `routes.py` | `get_current_user` | `AddRowRequest` (`row_data` object) | `DatasetManager.add_row()` | Row creation confirmation | Appends new records directly into the dataset file. |
| `DELETE` | `/api/datasets/{name}/rows/{idx}` | `routes.py` | `get_current_user` | Path param `idx` (integer) | `DatasetManager.delete_row()` | Deletion confirmation | Deletes a record by index from the dataset file. |
| `GET` | `/api/datasets/{name}/profile` | `quality_routes.py` | `get_current_user` | Path param `name` | `DataQualityService.profile_dataset()` | `ProfileResult` (column types, nulls, distinct counts) | Generates structural profiling data for UI metadata inspection. |
| `GET` | `/api/datasets/{name}/quality` | `quality_routes.py` | `get_current_user`, RateLimit (30/min) | `refresh` (boolean) | `DataQualityService.assess_dataset()` | `QualityAssessmentResult` (Score, Grade, Dimensions, Issues, Plan) | Comprehensive 6-dimension data quality assessment & health score. |
| `POST` | `/api/datasets/{name}/clean/preview` | `quality_routes.py` | `get_current_user`, RateLimit (20/min) | `CleaningPlanRequest` | `DataQualityService.preview_cleaning()` | Preview JSON (diff counts, before/after score delta, sample changes) | Zero-side-effect dry-run cleaning comparison before committing changes. |
| `POST` | `/api/datasets/{name}/clean` | `quality_routes.py` | `get_current_user`, RateLimit (10/min) | `CleaningPlanRequest` | `DataQualityService.apply_cleaning()` | `CleaningJob` object (`target_dataset`, `quarantine_dataset`, audit) | Executes cleaning pipeline, generates derived snapshot and quarantine file. |
| `GET` | `/api/datasets/{name}/lineage` | `quality_routes.py` | `get_current_user`, RateLimit (60/min) | Path param `name` | `DataQualityService.get_dataset_lineage()` | `DatasetLineage` (parent, children, versions, jobs) | Traces dataset derivation tree and version provenance across jobs. |
| `GET` | `/api/sessions` | `routes.py` | `get_current_user` | None | `SessionStore.list_sessions()` | `List[SessionResponse]` | Lists all conversation workspaces owned by authenticated user. |
| `POST` | `/api/sessions` | `routes.py` | `get_current_user` | `CreateSessionRequest` (`dataset_name`, `title`) | `SessionStore.create_session()` | `SessionResponse` | Initializes a new chat session scoped to a specific dataset. |
| `GET` | `/api/sessions/{session_id}` | `routes.py` | `get_current_user` | Path param `session_id` | `SessionStore.get_session()` | Session object + conversation `history` array | Retrieves session details and chat message turns. |
| `DELETE` | `/api/sessions/{session_id}` | `routes.py` | `get_current_user` | Path param `session_id` | `SessionStore.delete_session()` | `{"deleted": true, "session_id": "..."}` | Deletes session and associated conversation history. |
| `PATCH` | `/api/sessions/{id}/dataset` | `routes.py` | `get_current_user` | `SwitchSessionDatasetRequest` (`dataset_name`) | `SessionStore.switch_dataset()` | Updated `SessionResponse` | Hot-swaps the active dataset of a session (e.g. Raw $\leftrightarrow$ Clean v1). |
| `GET` | `/api/sessions/{id}/widgets` | `routes.py` | `get_current_user` | Path param `id` | `SessionStore.get_widgets()` | Array of pinned dashboard widget objects | Loads pinned visual widgets for the workspace dashboard. |
| `POST` | `/api/sessions/{id}/widgets` | `routes.py` | `get_current_user` | `CreateWidgetRequest` (`prompt`, `chart_type`) | `WidgetEngine.create_widget_from_prompt()` | Newly compiled widget object | Compiles user prompt into a live, recalculable dashboard widget. |
| `POST` | `/api/sessions/{id}/widgets/pin` | `routes.py` | `get_current_user` | `PinWidgetRequest` (`title`, `chart_svg`, spec) | `WidgetEngine.create_widget_from_chat()` | Pinned widget object | Pins a visual insight directly from chat conversation to the dashboard. |
| `POST` | `/api/sessions/{id}/widgets/recompute` | `routes.py` | `get_current_user` | `chart_theme` (light/dark) | `WidgetEngine.recompute_widgets()` | Array of updated widget objects | Recalculates all dashboard widgets with **0 LLM calls**. |
| `DELETE` | `/api/sessions/{id}/widgets/{w_id}` | `routes.py` | `get_current_user` | Path param `w_id` | `SessionStore.delete_widget()` | `{"deleted": true, "widget_id": "..."}` | Removes a widget from the dashboard. |
| `GET` | `/api/recent-graphs` | `routes.py` | `get_current_user` | `limit` (default 8) | Session turn and widget scanner | `List[RecentGraphInfo]` | Retrieves thumbnail previews of recent visualizations across sessions. |
| `GET` | `/api/dataset-changes` | `routes.py` | `get_current_user` | None | `DatasetManager.get_activity_log()` | List of activity log entries | Audit feed of data modifications, uploads, and clean derivations. |
| `GET` | `/api/suggestions` | `routes.py` | `get_current_user`, RateLimit (30/min) | `session_id`, `provider` | `call_llm` with `SUGGESTION_PROMPT` | Array of 4 recommended analytical questions | Context-aware query suggestions tailored to active dataset schema. |
| `POST` | `/api/ask` | `routes.py` | `get_current_user`, RateLimit (15/min) | `QuestionRequest` (`question`, `chart_type`, `provider`) | `AgentCoordinator.process_query()` | `AnalysisResponse` (summary, chart, spec, badge) | Main AI agent endpoint: routes intent, executes tools, attaches badge. |

---

## 4. Multi-Tenant Storage, Database & Cloud Resiliency Architecture

Visiq is engineered to run seamlessly across both cloud production (Railway + Supabase) and isolated local development environments without code changes.

```mermaid
flowchart TD
    subgraph DataStorageLayer["Storage Abstraction Layer"]
        subgraph FilePersistence["File Storage Abstraction (file_storage.py)"]
            F_ENV{"SUPABASE_SERVICE_KEY present?"}
            F_ENV -- Yes (Cloud Prod) --> SB_BUCKET["Supabase Storage Bucket ('visiq-uploads')"]
            F_ENV -- No (Local Dev) --> LOCAL_DIR["Local Filesystem Directory (data/uploads/{user_id}/)"]
        end

        subgraph DatabasePersistence["Relational Storage Abstraction (storage.py)"]
            D_ENV{"DATABASE_URL present?"}
            D_ENV -- Yes --> TRY_PG["Connect to Remote PostgreSQL (Supabase Pooler)"]
            TRY_PG -- Connection Succeeded --> PG_DB["Remote PostgreSQL with Row Level Security (RLS)"]
            TRY_PG -- psycopg.OperationalError (e.g. Paused) --> DB_FALLBACK["Self-Healing Fallback to SQLite"]
            D_ENV -- No --> SQLITE_DB["Local SQLite Engine (sqlite:///data/visiq.db)"]
            DB_FALLBACK --> SQLITE_DB
        end
    end

    subgraph DataIsolation["Multi-Tenant Isolation Model"]
        TENANT_KEY["Record Key Composition: (kind, owner_id, entity_name)"]
        TENANT_KEY --> RLS_POLICY["PostgreSQL RLS: owner = auth.uid()"]
        TENANT_KEY --> SQLITE_ISOL["SQLite Filter: WHERE owner = :user_id"]
    end

    SB_BUCKET --> DataIsolation
    LOCAL_DIR --> DataIsolation
    PG_DB --> DataIsolation
    SQLITE_DB --> DataIsolation
```

### Self-Healing Database Fallback Mechanism
1. **Cloud Production (`APP_ENV=production` & `RAILWAY_ENVIRONMENT`):** Connects to remote Supabase PostgreSQL via connection pooler (port `6543`), enforces Row Level Security (RLS), and revokes public permissions.
2. **Local Development Resilience:** If remote PostgreSQL is unreachable (such as when a free-tier Supabase project is paused or offline), [`backend/app/storage.py`](file:///c:/Users/ralph/Desktop/Projects/Data%20Analyst/Ai%20Data%20Analyst%20Agent/backend/app/storage.py) intercepts the `OperationalError`, logs a clear warning, clears the cached engine, and automatically initializes local SQLite storage at `data/visiq.db`.
3. **Zero-Latency Option:** Setting `DATABASE_URL=` in `.env` bypasses remote network handshakes entirely, booting the server in under 0.5 seconds.

---

## 5. Architectural Guardrails & Methodological Guarantees

1. **Additive Error Benchmark Integrity:** Injected benchmark defects (duplicates, negative prices, invalid keys) are designed to be additive on top of clean ground truth. Deterministic deduplication and outlier quarantine restore ground truth without lowering the theoretical accuracy ceiling.
2. **Zero LLM Prompt Contamination:** Quality health badges (`Computed on cleaned version (score: 96/100, Grade A)`) are deterministically resolved in the API route handler *outside* the LLM prompt context. The LLM receives only clean dataset schemas and filtered records, ensuring unbiased reasoning.
3. **Strict Zero-`eval()` Security Boundary:** The agent never generates or executes raw Python scripts. All operations translate into strict, parameterized calls to pre-compiled Pandas functions registered in `ToolRegistry`.
4. **Non-Destructive Lineage Tracking:** Cleaning operations never mutate original source files. Every cleaning run produces a versioned child snapshot (`__clean_v1.csv`), an optional quarantine file (`__quarantine_v1.csv`), and an immutable audit job record.
5. **Atomic Quota & Sliding-Window Rate Limiting:** In-memory sliding-window rate limiters prevent API spam on expensive endpoints (`/api/ask`, `/api/upload`), while the `QuotaManager` atomically tracks daily token consumption across LLM model rotations.

