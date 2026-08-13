with source as (
    select * from "tfm_mobility"."landing"."trip_records"
),

typed as (
    select
        md5(concat_ws('|', source_kind, source_file_id::text, source_row_number::text)) as trip_id,
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
        dispatching_base_num,
        hvfhs_license_num,
        extract(epoch from (dropoff_datetime - pickup_datetime)) / 60.0 as duration_minutes,
        loaded_at,
        case
            when pickup_datetime is null then 'missing_pickup_datetime'
            when dropoff_datetime is null then 'missing_dropoff_datetime'
            when dropoff_datetime < pickup_datetime then 'dropoff_before_pickup'
            when pickup_location_id is null then 'missing_pickup_location'
            when dropoff_location_id is null then 'missing_dropoff_location'
            when pickup_location_id not between 1 and 265 then 'invalid_pickup_location'
            when dropoff_location_id not between 1 and 265 then 'invalid_dropoff_location'
            when trip_distance < 0 then 'negative_trip_distance'
            when total_amount < 0 then 'negative_total_amount'
            else null
        end as invalid_reason
    from source
)

select * from typed