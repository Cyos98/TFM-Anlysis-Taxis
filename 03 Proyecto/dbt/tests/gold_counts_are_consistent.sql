select *
from {{ ref('fact_zone_hourly_demand') }}
where trip_count <= 0
   or revenue_observation_count < 0
   or revenue_observation_count > trip_count
