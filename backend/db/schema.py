"""
Supabase table definitions.

Run the SQL below once in the Supabase SQL Editor
(https://supabase.com/dashboard/project/<your-ref>/sql) to create the schema.

Paste and execute:

  create table if not exists postings (
    id          bigserial primary key,
    source      text not null,
    source_url  text not null,
    external_id text not null,
    company     text,
    company_domain text,
    title       text,
    description text,
    location_raw text,
    remote_type text,
    role_family text,
    posted_at   timestamptz,
    fetched_at  timestamptz default now(),
    constraint uq_source_external_id unique (source, external_id)
  );

  create table if not exists verifications (
    id                          bigserial primary key,
    posting_id                  bigint references postings(id) unique not null,
    trust_score                 integer,
    genuinely_remote            boolean,
    remote_confidence           float,
    scam_likelihood             float,
    scam_reasons                jsonb default '[]',
    role_clarity                float,
    employer_legitimacy_signals jsonb default '[]',
    newcomer_friendly_signals   jsonb default '[]',
    rationale                   text,
    llm_response_json           jsonb,
    classifier_version          text default '1.0',
    verified_at                 timestamptz default now()
  );

  create table if not exists feedback (
    id         bigserial primary key,
    posting_id bigint references postings(id) not null,
    user_id    text default 'anonymous',
    signal     text,
    note       text,
    created_at timestamptz default now()
  );
"""

# No ORM models needed — Supabase client handles all DB access.
# This file is kept as the single source of truth for the schema SQL.
