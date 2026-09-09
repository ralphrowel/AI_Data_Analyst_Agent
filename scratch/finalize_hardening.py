from pathlib import Path
import re
p=Path('backend/app/api/routes.py');s=p.read_text();s=re.sub(r'^.*default_quota_manager.record_usage\(.*\)\n','',s,flags=re.M)
# Preserve meaningful HTTP status codes from quota enforcement.
s=s.replace('    except Exception as e:\n', '    except HTTPException:\n        raise\n    except Exception as e:\n')
# Nested uploads need correctly indented handlers.
s=s.replace('        except HTTPException:\n        raise\n    except Exception as e:', '        except HTTPException:\n            raise\n        except Exception as e:')
p.write_text(s)
p=Path('backend/app/rag/indexer.py');s=p.read_text().replace('        docs = []','        docs = []',1);s=s.replace('                    with open(file_path,','                    from backend.app.paths import inside\n                    file_path = inside(self.knowledge_dir, file_path.name)\n                    with open(file_path,');p.write_text(s)
p=Path('README.md');s=p.read_text();s=s.replace('| LLM (primary) | Google Gemini free tier (`gemini-2.5-flash`) |','| LLM (primary) | Groq (`openai/gpt-oss-120b`) |').replace('| LLM (fallback) | Groq free tier (`llama-3.3-70b-versatile`) — auto-switches when Gemini\'s daily quota is hit |','| LLM (alternate/fallback) | Google Gemini (`gemini-2.5-flash`) |')
s=re.sub(r'- \*\*LLM fallback\*\*.*', '- **LLM fallback** — Groq is the configured default; Gemini is used when Groq fails and a Gemini key is available. When Gemini is selected, quota errors may fall back to Groq.',s)
s=s.replace('Set `GEMINI_API_KEY`, `GROQ_API_KEY`, and `ALLOWED_ORIGINS` in `.env` before starting the backend.', '''Copy `.env.example` to `.env` and `frontend/.env.example` to `frontend/.env.local`.
Configure `DATABASE_URL` for PostgreSQL (Supabase Postgres is supported), Supabase auth, at least one LLM key, and allowed frontend origins. Run `python -m backend.app.storage` before starting the API to initialize the schema. Use a migration/admin database account for initialization and a restricted application account at runtime. The backend fails startup if the database or schema is unavailable.

Set `VITE_API_BASE_URL` to your backend URL before building. If omitted, requests use the frontend origin. Frontend variables are public: never put database credentials or JWT signing secrets in `VITE_*` variables.

All `/api/*` routes require a valid Supabase access token. Asymmetric tokens use the configured project's JWKS; legacy HS256 projects can set `SUPABASE_JWT_SECRET`. Both paths require issuer, audience, expiry, issued-at, subject, and authenticated role. Demo profiles require **both** backend `APP_ENV=development` / `ALLOW_DEMO_AUTH=true` and frontend development mode / `VITE_ALLOW_DEMO_AUTH=true`. No guest or unverified-token fallback exists.

Users, chat sessions (history/widgets/usage), daily quotas, activity, and dataset metadata live in the PostgreSQL `app_records` table. This is a backend-only table: do not grant browser/anon/authenticated roles direct access. CSV and knowledge content still live on disk; use a persistent shared volume across workers and back it up. Shared sample datasets are copied into the user's private directory when edited. Knowledge uploads and indexes are private to each user.

Existing `data/quotas.json` is no longer read. Previously in-memory sessions cannot be recovered after their process exits. Existing private CSV files are discovered and their metadata persisted when listed. Back up old quota records before rollout; migrate them explicitly if preserving today's allowance matters. Previously shared knowledge uploads need an explicit owner before being moved into a user's knowledge directory.

Uploads default to 5 MiB of UTF-8 content (`MAX_UPLOAD_BYTES`); the request body has a separate bounded JSON envelope. Filenames must be plain basenames and resolved paths must stay within storage roots. All successful LLM calls—including routing, suggestions, and widgets—count toward the UTC daily quota. Each call checks remaining allowance; the last in-flight call can exceed the remaining budget because usage is reported after generation.

Run deterministic checks with `pip install -r requirements-dev.txt` and `python -m pytest`. Tests use isolated SQLite by default and no live LLM credentials. Set `TEST_DATABASE_URL` to a **disposable** PostgreSQL database to test its actual locking and persistence; the test fixture clears its application records. GitHub Actions runs the suite against PostgreSQL 16 and builds the frontend. Live Supabase OAuth and provider availability require separate deployment smoke testing.''')
s=s[:s.index('## Notes')]+'''## Operational notes

Structured request logs contain request IDs, method, status, and duration, without authorization headers or request bodies. Validation failures and production errors return generic messages.

Provider pricing and quotas depend on your accounts. Configure spending limits directly with each provider.
''';p.write_text(s)
p=Path('docs/implementation_plan_v1.md');s=p.read_text().replace('| Current Task |','| Completed    |');s+='''

### Security and persistence follow-up (2026-09-10)

Step 9 implementation now requires authenticated private routes and verified Supabase tokens. Demo identities are explicitly development-only. PostgreSQL backs users, sessions, quota records, activity, and dataset metadata; private RAG and safe bounded uploads replace shared uploads. Automated pytest regression and PostgreSQL CI replace the scratch verification scripts. See README setup and rollout notes; live OAuth/provider smoke checks depend on deployment credentials.
''';p.write_text(s)
# Retire the scratch runners in favor of deterministic, collected pytest suites.
for p in Path('scratch').glob('test_*.py'):
    p.write_text('"""Compatibility runner: regression coverage now lives in tests/."""\nif __name__ == "__main__":\n    import subprocess\n    import sys\n    from pathlib import Path\n    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest"], cwd=Path(__file__).resolve().parents[1]))\n')
