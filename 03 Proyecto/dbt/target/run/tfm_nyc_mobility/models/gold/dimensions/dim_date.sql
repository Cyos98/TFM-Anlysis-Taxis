
  
    

  create  table "tfm_mobility"."gold"."dim_date__dbt_tmp"
  
  
    as
  
  (
    with bounds as (
    select
        min(pickup_datetime::date) as first_date,
        max(pickup_datetime::date) as last_date
    from "tfm_mobility"."silver"."trips"
),

dates as (
    select generate_series(first_date, last_date, interval '1 day')::date as full_date
    from bounds
    where first_date is not null
)

select
    to_char(full_date, 'YYYYMMDD')::integer as date_key,
    full_date,
    extract(year from full_date)::smallint as year,
    extract(quarter from full_date)::smallint as quarter,
    extract(month from full_date)::smallint as month,
    extract(day from full_date)::smallint as day_of_month,
    extract(isodow from full_date)::smallint as iso_day_of_week,
    trim(to_char(full_date, 'Day')) as day_name,
    extract(week from full_date)::smallint as iso_week,
    extract(isodow from full_date) in (6, 7) as is_weekend
from dates
  );
  