# DATABASE_DESIGN.md

## Tech Stack
- DB: PostgreSQL 16+
- ORM: SQLAlchemy / Alembic
- Naming: `snake_case`
- IDs: UUID (`gen_random_uuid()`) for domain tables, bigint optional for logs
- Soft delete: `deleted_at` nullable timestamp on mutable business tables
- Audit columns: `created_at`, `updated_at`, `created_by`, `updated_by`

## ERD (high-level)
- `roles` 1-* `users`
- `users` 1-* `refresh_tokens`
- `loan_assessments` 1-1 `applicant_profiles`
- `loan_assessments` 1-1 `applicant_employment_infos`
- `loan_assessments` 1-1 `applicant_financial_infos`
- `loan_assessments` 1-* `applicant_debt_infos`
- `loan_assessments` 1-* `risk_results` (versioned results)
- `risk_results` 1-* `risk_factors`
- `risk_results` 1-* `risk_recommendations`
- `loan_assessments` 1-* `assessment_status_logs`

---

## Table: `roles`
Purpose: role master

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| code | varchar(30) | no | - | UNIQUE (`ADMIN`,`ANALYST`) |
| name | varchar(100) | no | - | - |
| created_at | timestamptz | no | now() | - |

---

## Table: `users`
Purpose: admin/analyst login users

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| role_id | uuid | no | - | FK -> roles.id, idx |
| username | varchar(60) | no | - | UNIQUE |
| email | varchar(120) | no | - | UNIQUE |
| password_hash | varchar(255) | no | - | - |
| full_name | varchar(150) | no | - | idx |
| status | varchar(20) | no | `ACTIVE` | idx |
| force_change_password | boolean | no | false | - |
| last_login_at | timestamptz | yes | null | - |
| created_at | timestamptz | no | now() | - |
| updated_at | timestamptz | no | now() | - |
| deleted_at | timestamptz | yes | null | idx |

Enum `status`: `ACTIVE`, `SUSPENDED`, `DISABLED`

---

## Table: `refresh_tokens`
Purpose: manage refresh sessions

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| user_id | uuid | no | - | FK -> users.id, idx |
| token_hash | varchar(255) | no | - | UNIQUE |
| user_agent | varchar(255) | yes | null | - |
| ip_address | varchar(64) | yes | null | - |
| expires_at | timestamptz | no | - | idx |
| revoked_at | timestamptz | yes | null | idx |
| created_at | timestamptz | no | now() | - |

---

## Table: `loan_assessments`
Purpose: assessment header + lifecycle

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_no | varchar(30) | no | generated | UNIQUE |
| created_by_user_id | uuid | no | - | FK -> users.id, idx |
| assigned_to_user_id | uuid | yes | null | FK -> users.id |
| status | varchar(20) | no | `DRAFT` | idx |
| source_channel | varchar(20) | no | `WEB` | idx |
| current_step | smallint | no | 1 | - |
| submitted_at | timestamptz | yes | null | idx |
| completed_at | timestamptz | yes | null | idx |
| latest_result_id | uuid | yes | null | FK -> risk_results.id |
| note | text | yes | null | - |
| created_at | timestamptz | no | now() | idx |
| updated_at | timestamptz | no | now() | - |
| deleted_at | timestamptz | yes | null | idx |

Enum `status`: `DRAFT`, `IN_PROGRESS`, `SUBMITTED`, `COMPLETED`, `CANCELLED`, `RE_EVALUATED`

---

## Table: `applicant_profiles`
Purpose: applicant personal info

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_id | uuid | no | - | FK -> loan_assessments.id, UNIQUE |
| first_name | varchar(120) | no | - | idx |
| last_name | varchar(120) | no | - | idx |
| national_id_hash | varchar(128) | yes | null | idx |
| date_of_birth | date | no | - | idx |
| age_years_snapshot | smallint | no | - | - |
| marital_status | varchar(20) | yes | null | idx |
| province_code | varchar(10) | no | - | FK -> provinces.code |
| district | varchar(120) | yes | null | - |
| postal_code | varchar(10) | yes | null | - |
| created_at | timestamptz | no | now() | - |
| updated_at | timestamptz | no | now() | - |

---

## Table: `applicant_employment_infos`
Purpose: job/income stability

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_id | uuid | no | - | FK -> loan_assessments.id, UNIQUE |
| occupation_code | varchar(40) | no | - | FK -> occupations.code |
| employment_type | varchar(20) | no | - | idx |
| employer_name | varchar(160) | yes | null | - |
| job_tenure_months | int | no | 0 | - |
| monthly_income | numeric(14,2) | no | 0 | idx |
| additional_income | numeric(14,2) | no | 0 | - |
| income_stability_score | numeric(5,2) | yes | null | - |
| created_at | timestamptz | no | now() | - |
| updated_at | timestamptz | no | now() | - |

---

## Table: `applicant_financial_infos`
Purpose: loan + aggregate financial data

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_id | uuid | no | - | FK -> loan_assessments.id, UNIQUE |
| requested_loan_amount | numeric(14,2) | no | - | idx |
| loan_term_months | int | no | - | - |
| loan_purpose_code | varchar(40) | no | - | FK -> loan_purposes.code |
| monthly_debt_payment | numeric(14,2) | no | 0 | - |
| existing_loan_balance | numeric(14,2) | no | 0 | - |
| debt_service_ratio | numeric(7,4) | yes | null | idx |
| net_monthly_income | numeric(14,2) | yes | null | - |
| created_at | timestamptz | no | now() | - |
| updated_at | timestamptz | no | now() | - |

---

## Table: `applicant_debt_infos`
Purpose: debt breakdown

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_id | uuid | no | - | FK -> loan_assessments.id, idx |
| debt_type | varchar(30) | no | - | idx |
| creditor_name | varchar(120) | yes | null | - |
| outstanding_amount | numeric(14,2) | no | 0 | - |
| monthly_payment | numeric(14,2) | no | 0 | - |
| delinquent_days | int | no | 0 | - |
| is_defaulted | boolean | no | false | idx |
| created_at | timestamptz | no | now() | - |
| updated_at | timestamptz | no | now() | - |

---

## Table: `risk_results`
Purpose: versioned result record per assessment

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_id | uuid | no | - | FK -> loan_assessments.id, idx |
| result_version | int | no | 1 | UNIQUE with assessment_id |
| model_version | varchar(80) | no | - | idx |
| score | numeric(6,2) | no | - | idx |
| score_scale | int | no | 100 | - |
| credit_score | int | yes | null | idx |
| score_grade | varchar(5) | yes | null | idx |
| default_probability | numeric(8,6) | yes | null | idx |
| risk_level | varchar(10) | no | - | idx |
| recommendation_type | varchar(20) | no | - | idx |
| primary_reason | text | yes | null | - |
| decision_note | text | yes | null | - |
| calculated_by | varchar(20) | no | `MODEL` | - |
| created_at | timestamptz | no | now() | idx |

---

## Table: `risk_factors`
Purpose: explainability factors

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| risk_result_id | uuid | no | - | FK -> risk_results.id, idx |
| factor_code | varchar(50) | no | - | idx |
| factor_label_th | varchar(200) | no | - | - |
| factor_label_en | varchar(200) | yes | null | - |
| impact_direction | varchar(10) | no | - | - |
| impact_score | numeric(6,2) | no | 0 | - |
| detail | text | yes | null | - |
| created_at | timestamptz | no | now() | - |

---

## Table: `risk_recommendations`
Purpose: action recommendations

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| risk_result_id | uuid | no | - | FK -> risk_results.id, idx |
| recommendation_type | varchar(20) | no | - | idx |
| title_th | varchar(200) | no | - | - |
| description_th | text | no | - | - |
| priority | smallint | no | 3 | - |
| is_primary | boolean | no | false | - |
| created_at | timestamptz | no | now() | - |

---

## Table: `assessment_status_logs`
Purpose: state transition audit

| field | type | null | default | key/index |
|---|---|---:|---|---|
| id | uuid | no | gen_random_uuid() | PK |
| assessment_id | uuid | no | - | FK -> loan_assessments.id, idx |
| from_status | varchar(20) | yes | null | - |
| to_status | varchar(20) | no | - | idx |
| changed_by_user_id | uuid | yes | null | FK -> users.id |
| reason | varchar(255) | yes | null | - |
| created_at | timestamptz | no | now() | idx |

---

## Lookup Tables

### `provinces`
- `code` PK (`varchar(10)`), `name_th`, `name_en`, `region`

### `occupations`
- `code` PK, `name_th`, `name_en`, `risk_weight` numeric(5,2), `is_active`

### `loan_purposes`
- `code` PK, `name_th`, `name_en`, `risk_weight`, `is_active`

### `income_ranges`
- `code` PK, `min_income`, `max_income`, `label_th`, `label_en`

### `recommendation_templates`
- `id` PK, `recommendation_type`, `risk_level`, `title_th`, `description_th`, `is_active`

### `risk_rule_templates`
- `id` PK, `rule_code`, `rule_name`, `conditions_json` (jsonb), `score_delta`, `priority`, `is_active`

---

## Existing Table Compatibility (current backend)
Current backend already has `prediction_logs`:
- keep table for backward compatibility + troubleshooting
- optional: map `prediction_logs` as `inference_logs` in final architecture
- long term: move to `loan_assessments` + `risk_results` as canonical source

---

## Indexing Strategy (important)
- `loan_assessments(assessment_no)` unique
- `loan_assessments(status, created_at desc)`
- `risk_results(assessment_id, result_version desc)`
- `risk_results(risk_level, created_at desc)`
- `applicant_profiles(first_name, last_name)` full-text optional
- `users(email)`, `users(username)` unique

## Partitioning / Retention (optional prod)
- partition `assessment_status_logs` and `inference_logs` by month if volume high
- retention for detailed logs: 12-24 months based on policy
