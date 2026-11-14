# mock-AD: Samba AD DC с тестовыми пользователями — только для разработки (SPEC §6.2, §18.1).
FROM debian:bookworm-20251103-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        samba samba-ad-dc samba-ad-provision samba-dsdb-modules samba-vfs-modules \
        winbind krb5-user ldb-tools \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/samba/smb.conf

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY users.tsv /seed/users.tsv
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 389 636
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
