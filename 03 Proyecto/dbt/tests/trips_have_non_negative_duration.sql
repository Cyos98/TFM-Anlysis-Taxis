select trip_id
from {{ ref('trips') }}
where duration_minutes < 0
