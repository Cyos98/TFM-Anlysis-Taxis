select *
from (
    values
        ('yellow', 'Yellow Taxi', true, true),
        ('green', 'Green Taxi', true, true),
        ('fhv', 'For-Hire Vehicle', false, false),
        ('fhvhv', 'High Volume For-Hire Vehicle', true, true)
) as services (
    service_type_key,
    service_type_name,
    supports_distance,
    supports_observed_amount
)