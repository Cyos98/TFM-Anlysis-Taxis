
  
    

  create  table "tfm_mobility"."gold"."fact_zone_daily_performance__dbt_tmp"
  
  
    as
  
  (
    select
    md5(concat_ws(
        '|',
        pickup_datetime::date::text,
        pickup_location_id::text,
        service_type
    )) as zone_day_service_key,
    to_char(pickup_datetime::date, 'YYYYMMDD')::integer as date_key,
    pickup_location_id as taxi_zone_key,
    service_type as service_type_key,
    count(*)::bigint as trip_count,
    count(total_amount)::bigint as revenue_observation_count,
    sum(total_amount) as observed_trip_amount,
    avg(duration_minutes) as average_duration_minutes,
    avg(trip_distance) as average_trip_distance,
    avg(
        case
            when duration_minutes > 0 and trip_distance is not null
                then trip_distance / (duration_minutes / 60.0)
        end
    ) as average_speed_mph,
    sum(duration_minutes) / 60.0 as occupied_hours
from "tfm_mobility"."silver"."trips"
group by 2, 3, 4, pickup_datetime::date
  );
  