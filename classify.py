import argparse
import os
import re

import icalendar

import template_variables


def classify_in_place(db, rules_dir):
    rules = load_rules(db, rules_dir)

    for classification, sql in rules:
        db.execute(sql)
        v_ids = [r[0] for r in db.fetchall()]
        db.executemany('insert into classifications (vevent_id, classification) values (?, ?)',
                       [(v_id, classification) for v_id in v_ids])

    
def rule_name(fname):
    f = os.path.split(fname)[-1]
    return f[:f.rfind('.sql')]
    
        
def load_rules(db, rules_dir):
    sql_fnames = [os.path.join(rules_dir, fname) for fname in os.listdir(rules_dir) if fname.endswith('.sql')]
    return sorted([(rule_name(fname), template_variables.render_file(db, fname)) 
                   for fname in sql_fnames])

 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rules_dir")
    parser.add_argument("db_file")

    args = parser.parse_args()
    with repo.connect(args.db_file) as db:
        classify_in_place(db, args.rules_dir)


    

if __name__ == '__main__':
    main()
