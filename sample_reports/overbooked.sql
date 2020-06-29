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

overlapping_pairs as (

  select
    v1.vevent_id as vevent1_id,
    v2.vevent_id as vevent2_id,
    v1.dtstart as dtstart1,
    v1.dtend as dtend1,
    v2.dtstart as dtstart2,
    v2.dtend as dtend2
  from
    vevents v1 cross join vevents v2
  where
    v1.vevent_id != v2.vevent_id and
    v1.dtstart <= v2.dtstart and
    v2.dtstart < v1.dtend

),

overlapping_edges as (

  select
    dtstart2 as start_edge_dt,
    case
      when dtend1 < dtend2 then dtend1
      else dtend2
    end as stop_edge_dt
  from
    overlapping_pairs

),

overlapping_hours as (

  select
    (julianday(stop_edge_dt) - julianday(start_edge_dt)) * 24 as hours
  from
    overlapping_edges

)

select
  (select count(*) from overlapping_pairs) as double_booked_pairs,
  (select sum(hours) from overlapping_hours) as double_booked_hours;
