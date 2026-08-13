select
    location_id as taxi_zone_key,
    borough,
    zone_name,
    service_zone
from {{ ref('taxi_zone_lookup') }}
