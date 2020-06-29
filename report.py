import argparse
from collections import OrderedDict
import os
import re

import icalendar

import template_variables


def run_reports(db, reports):
    for report, sql in reports:
        db.execute(sql)
        res = db.fetchall()
        if not res:
            yield report, dict(columns=[], rows=[])
        else:
            columns = res[0].keys()
            yield report, dict(columns=columns, rows=[tuple(r) for r in res])

        
def report_name(fname):
    f = os.path.split(fname)[-1]
    return f[:f.rfind('.sql')]

    
def load_reports(db, reports_dir):
    sql_fnames = [os.path.join(reports_dir, fname) for fname in os.listdir(reports_dir) if fname.endswith('.sql')]
    return sorted([(report_name(fname), template_variables.render_file(db, fname)) 
                   for fname in sql_fnames])


def render_results(db, results, format_file):
    extra_context = dict(reports=results)
    return template_variables.render_file(db, format_file, extra_context=extra_context)


def render_reports(db, reports_dir, format_file):
    reports = load_reports(db, reports_dir)
    results = run_reports(db, reports)
    return render_results(db, results, format_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reports_dir")
    parser.add_argument("db_file")
    parser.add_argument("format_file")

    args = parser.parse_args()
    with repo.connect(args.db_file) as db:
        print(render_reports(db, args.reports_dir, args.format_file))

    

if __name__ == '__main__':
    main()
