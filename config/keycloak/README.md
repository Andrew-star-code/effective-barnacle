# Конфигурация Keycloak

Realm `corp` без секретов и русская тема входа (SPEC §6.3).

- `realm-corp.dev.json` — есть: realm для dev-стека, импортируется при первом старте `keycloak`
  (`--import-realm`; если realm уже есть — не перезаписывается). Федерация LDAP к mock-AD (`READ_ONLY`, импорт включён,
  `sAMAccountName`, `objectGUID`, маппер MSAD account controls — отключённые в AD не входят), защита от перебора
  (5 попыток, блокировка на 15 минут), события `LOGIN`/`LOGIN_ERROR`/`LOGOUT`, клиент `weknora`.
  Секреты подставляются из переменных окружения при импорте: `KC_WEKNORA_CLIENT_SECRET`, `KC_LDAP_BIND_PASSWORD`.
- Адреса в dev: браузер — `http://keycloak.localhost:8180` (админка — `/admin`, логин `admin`, пароль `KC_ADMIN_PASSWORD`),
  WeKnora — `http://keycloak:8080`; issuer в токенах — фронтовый адрес (`KC_HOSTNAME`).

Планируется: `realm-export.json` для прода (LDAPS к AD), тема `themes/corp-ru/` — этап 1.
