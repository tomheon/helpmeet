import datetime
import os
import sqlite3

import pytest

from extract import is_vevent, is_accepted, safe_dt, store_attendees, store_vevent, is_individual, extract_from_file
import repo
import template_variables


@pytest.mark.parametrize("name,expected",
                         [('VEVENT', True),
                          ('Nope', False),
                          ('', False),
                          (None, False)])
def test_is_vevent(name, expected):
    class C:
        def __init__(self, name):
            self.name = name

    c = C(name)
    assert is_vevent(c) == expected


@pytest.mark.parametrize("partstat,expected",
                          [('ACCEPTED', True),
                           ('accepted', True),
                           ('Accepted', True),
                           ('accEpted', True),
                           ('Needs Action', False),
                           ('', False),
                           (None, False)])
def test_is_accepted(partstat, expected):
    class A:
        def __init__(self, parstat):
            self.params = dict()
            if parstat is not None:
                self.params['partstat'] = partstat

    a = A(partstat)
    assert is_accepted(a) == expected


@pytest.mark.parametrize("cutype,expected",
                          [('INDIVIDUAL', True),
                           ('individual', True),
                           ('Individual', True),
                           ('indiVidual', True),
                           ('RESOURCE', False),
                           ('', False),
                           (None, False)])
def test_is_individual(cutype, expected):
    class A:
        def __init__(self, cutype):
            self.params = dict()
            if cutype is not None:
                self.params['cutype'] = cutype

    a = A(cutype)
    assert is_individual(a) == expected


def test_safe_dt():
    class A:
        def __init__(self):
            self.dt = 'yes'

    d = dict()
    assert safe_dt(d, 'hello') is None
    a = A()
    d['hello'] = a
    assert safe_dt(d, 'hello') is 'yes'



class Attendee:

    def __init__(self, mailto, is_accepted):
        self.mailto = mailto
        self.params = dict()
        self.params['cutype'] = 'INDIVIDUAL'
        if is_accepted:
            self.params['partstat'] = 'ACCEPTED'
        else:
            self.params['partstat'] = 'DECLINED'

    def __str__(self):
        return self.mailto

    def is_accepted(self):
        return self.params['partstat'] == 'ACCEPTED'


DEFAULT_ATTENDEE = "default@example.com"
ATTENDEE_ACCEPTED = Attendee("aa@example.com", True)
SAME_ATTENDEE_DECLINED = Attendee("aa@example.com", False)
ATTENDEE_DECLINED = Attendee("ad@example.com", False)


@pytest.mark.parametrize("descrip,v_id,attendees,default_attendee,expected",
                         [("Default accepted used if empty attendees",
                           1, [], DEFAULT_ATTENDEE,
                           [(1, DEFAULT_ATTENDEE, True)]),
                         ("Default accepted used if None attendees",
                           1, None, DEFAULT_ATTENDEE,
                           [(1, DEFAULT_ATTENDEE, True)]),
                          ("Non-list attendee handled",
                           2, ATTENDEE_ACCEPTED, DEFAULT_ATTENDEE,
                           [(2, str(ATTENDEE_ACCEPTED), True)]),
                          ("Attendance is recorded",
                           3, ATTENDEE_DECLINED, DEFAULT_ATTENDEE,
                           [(3, str(ATTENDEE_DECLINED), False)]),
                          ("List attendance is recorded",
                           4, [ATTENDEE_ACCEPTED, ATTENDEE_DECLINED], DEFAULT_ATTENDEE,
                           [(4, str(ATTENDEE_ACCEPTED), True),
                            (4, str(ATTENDEE_DECLINED), False)]),
                          ("List attendance is recorded correctly with default attendee overlap",
                           4, [ATTENDEE_ACCEPTED, ATTENDEE_DECLINED], ATTENDEE_DECLINED.mailto,
                           [(4, str(ATTENDEE_ACCEPTED), True),
                            (4, str(ATTENDEE_DECLINED), False)]),
                         ])
def test_store_attendees(descrip, v_id, attendees, default_attendee, expected):
    with repo.init(":memory:") as db:
        store_attendees(db, v_id, attendees, default_attendee)
        db.execute('select vevent_id, attendee, accepted from attendees')
        res = db.fetchall()
        rows = [tuple(r) for r in res]

        assert sorted(rows) == sorted(expected)


@pytest.mark.parametrize("attendees",
                         [[ATTENDEE_ACCEPTED, ATTENDEE_ACCEPTED],
                          [ATTENDEE_ACCEPTED, SAME_ATTENDEE_DECLINED]])
def test_duplicate_attendees_errors(attendees):
    with repo.init(":memory:") as db:
        with pytest.raises(sqlite3.IntegrityError):
            store_attendees(db, 1, attendees, DEFAULT_ATTENDEE)


class DtWrap:

    def __init__(self, dt):
        self.dt = dt

    def __str__(self):
        return str(self.dt)


@pytest.mark.parametrize("recurrence_id",
                         ['123',
                          None])
def test_store_vevent(recurrence_id):
    vevent = dict(uid='uid1',
                         summary='This is a summary',
                         dtstart=DtWrap(datetime.datetime(2020, 1, 20, 5, 15)),
                         dtend=DtWrap(datetime.datetime(2020, 1, 20, 6, 15)),
                         organizer=str(ATTENDEE_ACCEPTED),
                         attendee=[ATTENDEE_ACCEPTED, ATTENDEE_DECLINED])
    vevent['recurrence-id'] = recurrence_id
    with repo.init(':memory:') as db:
        store_vevent(db, vevent, DEFAULT_ATTENDEE)
        db.execute('select * from vevents')
        res = db.fetchall()
        assert len(res) == 1
        row = res[0]
        for field in 'uid summary'.split():
            assert vevent[field] == row[field]
        for field in 'dtstart dtend'.split():
            assert str(vevent[field]) == row[field]
        assert vevent['organizer'] == row['organizer']
        assert bool(recurrence_id) == bool(row['is_recurring'])
        db.execute('select * from attendees')
        a_res = db.fetchall()
        assert len(a_res) == 2
        for a_row in a_res:
            assert a_row['vevent_id'] == row['vevent_id']
        assert sorted([(a['attendee'], a['accepted']) for a in a_res]) == \
            sorted([(str(a), a.is_accepted()) for a in [ATTENDEE_ACCEPTED, ATTENDEE_DECLINED]])


def test_extract_integration():
    fixture_fname = os.path.join('fixtures', 'test_calendar.ics')
    start_date = datetime.datetime(2020, 6, 1)
    end_date = datetime.datetime(2020, 7, 1)
    with repo.init(':memory:') as db:
        with open(fixture_fname, 'rb') as fh:
            extract_from_file(fh, start_date, end_date, None, db)
            # check that the expected template variables were set
            vars = template_variables.read_all(db)
            assert vars == dict(calendar_name='wnarmy@example.com', start_date=str(start_date),
                                end_date=str(end_date))
            # sample is constructed to test:
            #
            # - events that are missing dtstart or dtend don't show up
            # - events outside the select date range don't show up
            # - events that the owner hasn't accepted don't show up
            # - recurrence is recorded correctly
            db.execute('''select vevent_id, uid, summary,
                                 dtstart, dtend, is_recurring, organizer
                          from vevents
                          order by uid''')
            actual_vevents = db.fetchall()
            expected_vevents = [
                dict(vevent_id=2,
                     uid='7s0lmnog628m6r441ds5265rcm@example.com',
                     summary='Heads down',
                     dtstart='2020-06-25 14:00:00+00:00',
                     dtend='2020-06-25 15:50:00+00:00',
                     is_recurring=0,
                     organizer=None),
                dict(vevent_id=1,
                     uid='ptbs4a3gd96g22tcgeoh2fam74_R20200514T200000@example.com',
                     summary='Examine heffalumps',
                     dtstart='2020-06-25 16:00:00-04:00',
                     dtend='2020-06-25 17:35:00-04:00',
                     is_recurring=1,
                     organizer='mailto:mwilkins@example.com'),
            ]
            assert [dict(r) for r in actual_vevents] == expected_vevents

            # sample is constructed to test:
            #
            # - meetings with no attendees show the calendar owner as attending
            # - acceptance status is recorded
            # - meetings that don't have the calendar owner aren't treated specially
            db.execute('''select vevent_id, attendee, accepted from attendees
                          order by vevent_id, attendee''')
            actual_attendees = db.fetchall()
            expected_attendees = [
                dict(vevent_id=1,
                     attendee='mailto:jjones@example.com',
                     accepted=0),
                dict(vevent_id=1,
                     attendee='mailto:klully@example.com',
                     accepted=1),
                dict(vevent_id=1,
                     attendee='mailto:mwilkins@example.com',
                     accepted=1),
                dict(vevent_id=2,
                     attendee='wnarmy@example.com',
                     accepted=1),
            ]

            assert[dict(r) for r in actual_attendees] == expected_attendees
