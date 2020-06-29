with

days_spent as (

  select
    vevent_id,
    julianday(dtend) - julianday(dtstart) as days
  from
    vevents natural join attendees
  where
    dtstart is not null and dtend is not null
    and attendee like '%{{ calendar_owner|default(calendar_name) }}%'
    and accepted = 1
    
),

rollups_by_classification as (

  select
    c.classification as classification,
    sum(d.days) * 24 as hours
  from
    days_spent d natural join classifications c
  group by
    c.classification
  order by
    days desc

)

select * from rollups_by_classification;
    
