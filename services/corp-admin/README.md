# corp-admin

SPA админки для разделов, которых нет в WeKnora (SPEC §15): переписка, инциденты, лимиты, входы, группы.
Vue 3 + TypeScript (strict) + Vite + TDesign — тот же стек, что у фронтенда WeKnora.

Сейчас это каркас этапа 0: роутинг, layout, TDesign с русской локалью, i18n, типизированный клиент API.

```bash
pnpm install --frozen-lockfile
pnpm dev          # http://localhost:5174/corp-admin/, /corp/api проксируется на corp-ext (CORP_EXT_URL)
pnpm typecheck && pnpm test && pnpm build
pnpm gen-api      # src/api/schema.d.ts из openapi.json (обычно через `make gen-api` из корня)
```

- Страницы — `src/pages/`, маршруты — `src/router/index.ts`, меню — `src/router/navigation.ts`.
- Все строки — через i18n (`src/i18n/locales/ru.ts`), русский по умолчанию.
- `openapi.json` и `src/api/schema.d.ts` генерируются из `corp-ext`; руками не правятся.
- Вход через Keycloak и проверка прав — этап 1.
