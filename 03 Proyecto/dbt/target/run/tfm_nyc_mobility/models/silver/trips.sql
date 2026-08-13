
  
    

  create  table "tfm_mobility"."silver"."trips__dbt_tmp"
  
  
    as
  
  (
    select
    trip_id,
    source_kind,
    source_file_id,
    source_filename,
    source_row_number,
    service_type,
    pickup_datetime,
    dropoff_datetime,
    pickup_location_id,
    dropoff_location_id,
    trip_distance,
    total_amount,
    duration_minutes,
    dispatching_base_num,
    hvfhs_license_num,
    loaded_at
from "tfm_mobility"."staging"."stg_trip_records"
where invalid_reason is null
  );
  