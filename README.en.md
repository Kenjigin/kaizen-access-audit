# IT Access Audit · Kaizen Logística

[Versión en español](README.md)

Personal project, in progress. I'm really interested in data and information security, and I wanted to bring both together by learning how an IT access audit works: the kind of review risk and audit teams do to check who has access to what inside a company.

Since I can't use real data, I made up a company: Kaizen Logística, a delivery company that hires temporary staff for Cyber Day and Christmas. The problem I want to show is a common one: people leave, but their accounts stay active, and during peak season people get extra permissions that nobody removes afterwards.

## The problem

In many companies, access reviews are done by hand, in Excel sheets, once a year. That means an account that should have been closed in January can stay open until December without anyone noticing. In the meantime, that account can still see customer data or approve payments.

What motivated me was the idea that this can be checked automatically and often, not only when the audit comes around. It would help mostly companies with high staff turnover, like retail and logistics, and their IT and internal audit teams, who need to prove they control who gets into their systems. In the end it also protects the people whose data those companies store, which is exactly what Chile's new data protection law (Ley 21.719) is about.

## How I built it

I set up an Oracle database and a Python script that fills the company with employees, accounts, roles and change tickets. When it generates the data, it hides some errors on purpose, and then I look for them with SQL queries, the way an auditor would.

## Controls

| Code | What I check | Status |
| --- | --- | --- |
| AC-01 | Former employees who still have an active account | Done |
| AC-02 | Users with conflicting permissions (segregation of duties) | Pending |
| AC-03 | Admin accounts outside IT and generic accounts | Pending |
| AC-04 | Accounts unused for more than 90 days | Pending |
| CM-01 | Production changes without approval | Pending |

I use ISO/IEC 27001:2022 and Chile's Personal Data Protection Law (Ley 21.719) as reference.

## What's in the repo

```
database/          table creation
data_generator/    fake data generator
audit_tests/       one SQL query per control
```

Built with Oracle Database Free on Docker, SQL and Python (oracledb and Faker).

## How to try it

1. Start Oracle with the `gvenzl/oracle-free` image and create the `kaizen` user.
2. Run `database/01_create_tables.sql`.
3. Install `oracledb` and `faker`, then run `data_generator/generar_datos.py`.
4. Try the queries in `audit_tests/` with any SQL client.

## What's next

Finish the remaining controls, automate them with Python, move the results to Excel, build a dashboard and write a final report with recommendations.

All the data is made up.

Claudio Galiano · Computer Engineering student, Duoc UC
