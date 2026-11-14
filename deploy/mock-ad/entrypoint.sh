#!/usr/bin/env bash
# Поднимает Samba AD DC домена CORP.LOCAL и при первом запуске заводит тестовых пользователей
# из /seed/users.tsv. Только для разработки: LDAP без TLS и простые пароли (SPEC §6.6).
set -euo pipefail

: "${MOCK_AD_ADMIN_PASSWORD:?MOCK_AD_ADMIN_PASSWORD не задан}"
: "${MOCK_AD_USER_PASSWORD:?MOCK_AD_USER_PASSWORD не задан}"
: "${MOCK_AD_BIND_PASSWORD:?MOCK_AD_BIND_PASSWORD не задан}"

BASE_DN="DC=corp,DC=local"
MARKER=/var/lib/samba/.seeded

if [[ ! -f /etc/samba/smb.conf ]]; then
  echo "mock-ad: provisioning domain CORP.LOCAL"
  rm -rf /var/lib/samba/private/* /var/lib/samba/sysvol/* 2>/dev/null || true
  samba-tool domain provision \
    --realm=CORP.LOCAL --domain=CORP --server-role=dc --dns-backend=SAMBA_INTERNAL \
    --host-name=dc1 --adminpass="$MOCK_AD_ADMIN_PASSWORD" \
    --option="dns forwarder = 127.0.0.1"
fi

# Простой bind без TLS (Keycloak и corp-ext в dev ходят на ldap://mock-ad:389). provision этот
# параметр в smb.conf не сохраняет, поэтому проставляем при каждом старте.
if ! grep -q 'ldap server require strong auth' /etc/samba/smb.conf; then
  sed -i '/^\[global\]/a\	ldap server require strong auth = no' /etc/samba/smb.conf
fi

if [[ ! -f "$MARKER" ]]; then
  echo "mock-ad: seeding users"
  samba-tool domain passwordsettings set --complexity=off --min-pwd-length=6 \
    --min-pwd-age=0 --max-pwd-age=0 --account-lockout-threshold=0

  samba-tool ou create "OU=Service Accounts,$BASE_DN"
  samba-tool ou create "OU=Staff,$BASE_DN"
  samba-tool user create svc-ai-assistant "$MOCK_AD_BIND_PASSWORD" \
    --userou="OU=Service Accounts" --description="Bind account for Keycloak and corp-ext"

  declare -A groups_seen=()
  while IFS=$'\t' read -r login first middle last email department title phone enabled groups; do
    [[ "$login" == "login" || -z "$login" ]] && continue
    samba-tool user create "$login" "$MOCK_AD_USER_PASSWORD" --userou="OU=Staff" --use-username-as-cn \
      --given-name="$first" --surname="$last" --mail-address="$email" \
      --department="$department" --job-title="$title" --telephone-number="$phone" \
      --company="ООО «Тестовая компания»"
    # middleName и displayName «Фамилия Имя Отчество» — как в корпоративном AD (SPEC §6.3).
    ldbmodify -H /var/lib/samba/private/sam.ldb <<EOF
dn: CN=$login,OU=Staff,$BASE_DN
changetype: modify
replace: middleName
middleName: $middle
-
replace: displayName
displayName: $last $first $middle
EOF
    [[ "$enabled" == "no" ]] && samba-tool user disable "$login"
    IFS=',' read -ra user_groups <<<"$groups"
    for group in "${user_groups[@]}"; do
      if [[ -z "${groups_seen[$group]:-}" ]]; then
        samba-tool group add "$group"
        groups_seen[$group]=1
      fi
      samba-tool group addmembers "$group" "$login"
    done
  done < /seed/users.tsv
  touch "$MARKER"
fi

exec samba --foreground --no-process-group
