with

vevents_accepted as (

  select
    vevent_id,
    dtstart,
    dtend
  from
    vevents natural join attendees
  where
    dtstart is not null and dtend is not null
    and attendee like '%{{ calendar_owner|default(calendar_name) }}%'
    and accepted = 1
    
),

attendees_and_hours as (

  select
    attendee,
    (julianday(dtend) - julianday(dtstart)) * 24 as hours
  from
    vevents_accepted natural join attendees
  where
    attendee not like '%{{ calendar_owner|default(calendar_name) }}%'

),

summed_hours as (
  select
    attendee,
    sum(hours) as hours
  from
    attendees_and_hours
  group by
    attendee

)

select * from summed_hours order by hours desc limit 10;
