# Sources

This file records outside code that the project borrows, where it is used, and its license.

| What was borrowed | Where it is used | Source | Version | License | Date read |
|---|---|---|---|---|---|
| The `react-ts` template of `create-vite`, made with the `--eslint` option. The demo page, its logos and its styles were removed. | `frontend/` | https://github.com/vitejs/vite/tree/main/packages/create-vite | `create-vite` 9.3.4 | MIT (https://github.com/vitejs/vite/blob/main/LICENSE) | 2026-11-23 |
| The password part of `backend/app/core/security.py` in the official FastAPI full-stack template: `pwdlib` with the Argon2 hasher. Changed on purpose: Argon2 only, with no bcrypt, and plain `verify` instead of `verify_and_update`. | `backend/app/security.py` | https://github.com/fastapi/full-stack-fastapi-template | commit `77e550a73bb49dd2967622c5ed11bf7a49603c93` (2026-11-16) | MIT (https://github.com/fastapi/full-stack-fastapi-template/blob/77e550a73bb49dd2967622c5ed11bf7a49603c93/LICENSE) | 2026-11-24 |
