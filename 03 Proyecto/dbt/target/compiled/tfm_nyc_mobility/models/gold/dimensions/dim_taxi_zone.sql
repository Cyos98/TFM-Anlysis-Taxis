select
    location_id as taxi_zone_key,
    borough,
    zone_name,
    service_zone
from "tfm_mobility"."reference"."taxi_zone_lookup"