select
    trip_id,
    to_char(pickup_datetime::date, 'YYYYMMDD')::integer as pickup_date_key,
    extract(hour from pickup_datetime)::smallint as pickup_hour_key,
    pickup_location_id as pickup_taxi_zone_key,
    dropoff_location_id as dropoff_taxi_zone_key,
    service_type as service_type_key,
    pickup_datetime,
    dropoff_datetime,
    duration_minutes,
    trip_distance,
    total_amount as observed_trip_amount,
    total_amount is not null as has_observed_amount,
    case
        when duration_minutes > 0 and trip_distance is not null
            then trip_distance / (duration_minutes / 60.0)
    end as average_speed_mph,
    source_kind,
    source_file_id,
    source_row_number
from "tfm_mobility"."silver"."trips"