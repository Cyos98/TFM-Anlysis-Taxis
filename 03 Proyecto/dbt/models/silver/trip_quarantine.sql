select
    *,
    current_timestamp as quarantined_at
from {{ ref('stg_trip_records') }}
where invalid_reason is not null
