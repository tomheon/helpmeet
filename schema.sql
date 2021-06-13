create table vevents (
  vevent_id integer primary key,
  uid text,
  summary text,
  description text,
  location text,
  dtstart text,
  dtend text,
  is_recurring integer,
  organizer text
);

create table attendees (
  vevent_id integer,
  attendee text,
  accepted integer,

  primary key (vevent_id, attendee)
);

create table classifications (
  vevent_id integer,
  classification text,
  primary key (vevent_id, classification)
);

create table template_variables (
  varname text primary key,
  varval
);
