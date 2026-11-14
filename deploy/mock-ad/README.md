# mock-AD

Samba AD DC домена `CORP.LOCAL` с тестовыми пользователями — для разработки без доступа к AD (SPEC §6.2, §6.6, §18.1).

- `Dockerfile` — Debian + Samba; `entrypoint.sh` при первом запуске создаёт домен, сервисную учётку
  `svc-ai-assistant` (bind для Keycloak и `corp-ext`) и пользователей из `users.tsv`; состояние — в томах `mock-ad-state`, `mock-ad-conf`.
- `users.tsv` — вымышленные сотрудники: ФИО с отчеством (`middleName`, `displayName` «Фамилия Имя Отчество»),
  email, отдел, должность, телефон, группы; `sidorov` отключён; `smirnov`/`smirnova` — однофамильцы.
  Пароли — `MOCK_AD_*` из `deploy/compose/.env.example`.
- Отличия от прода: LDAP без TLS (`ldap://mock-ad:389`, `ldap server require strong auth = no`), сложность паролей и блокировка
  в домене выключены, контейнеру нужен `SYS_ADMIN` (xattr в sysvol).

Пересоздать домен с нуля: `docker compose -f deploy/compose/compose.dev.yml down` и удалить тома `mock-ad-state`, `mock-ad-conf`.

Проверка: `ldapsearch -H ldap://localhost:3389 -D 'CN=svc-ai-assistant,OU=Service Accounts,DC=corp,DC=local' -w <пароль> -b DC=corp,DC=local '(sAMAccountName=ivanov)'`.
