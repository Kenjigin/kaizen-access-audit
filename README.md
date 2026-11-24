# kaizen-access-audit

Personal project (in progress). I'm simulating an IT access audit for a made-up logistics company called Kaizen Logistica S.A.

The idea: generate fake HR and ERP data with some errors on purpose (ex-employees with active accounts, too many permissions, unapproved changes) and then find them with SQL and Python.

Stack: Oracle Database Free on Docker, SQL, Python.

Done so far:
- database tables
- data generator
- first test: terminated employees with active accounts (AC-01)

Next: the other controls, Excel workpapers and a dashboard.
