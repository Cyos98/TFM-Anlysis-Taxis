#!/usr/bin/env bash
set -euo pipefail

start_date="${1:?start_date requerido}"
end_date="${2:?end_date requerido}"
services_csv="${3:?services requerido}"
base_url="${4:?base_url requerido}"

start_month="${start_date:0:7}"
end_month="${end_date:0:7}"
current="$start_month-01"
end="$end_month-01"

IFS=',' read -r -a services <<< "$services_csv"
while [[ "$current" < "$end" || "$current" == "$end" ]]; do
    year="${current:0:4}"
    month="${current:5:2}"
    for service in "${services[@]}"; do
        service="${service//[[:space:]]/}"
        filename="${service}_tripdata_${year}-${month}.parquet"
        printf '{"source_kind":"tlc","service_type":"%s","year":%s,"month":%s,"filename":"%s","source_url":"%s/%s"}\n' \
            "$service" "$year" "$((10#$month))" "$filename" "$base_url" "$filename"
    done
    current="$(date -u -d "$current +1 month" +%Y-%m-01)"
done
