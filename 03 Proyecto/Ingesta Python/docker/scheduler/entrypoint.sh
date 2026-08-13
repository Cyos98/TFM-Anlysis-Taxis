#!/bin/sh
set -eu

schedule="${TFM_SCHEDULE_CRON:-0 3 * * *}"
environment_file=/run/tfm-scheduler.env
cron_file=/etc/cron.d/tfm-pipeline

shell_quote() {
    printf "%s" "$1" | sed "s/'/'\"'\"'/g"
}

: > "$environment_file"
for variable in \
    TFM_ENVIRONMENT TFM_CONFIG_PATH TFM_DATA_ROOT TFM_LOGS_ROOT TFM_SQL_ROOT \
    TFM_DATABASE_HOST TFM_DATABASE_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD \
    DBT_PROFILES_DIR; do
    eval "value=\${$variable:-}"
    escaped="$(shell_quote "$value")"
    printf "export %s='%s'\n" "$variable" "$escaped" >> "$environment_file"
done
chown tfm:tfm "$environment_file"
chmod 0600 "$environment_file"

cat > "$cron_file" <<EOF
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin
${schedule} tfm . ${environment_file} && /app/scripts/run_scheduled_demo.sh
EOF
chmod 0644 "$cron_file"

exec cron -f
