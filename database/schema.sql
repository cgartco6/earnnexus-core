-- file: database/schema.sql
-- Drop tables if they exist to provide a clean, complete initialization run path
drop table if exists public.transaction_ledger;

-- Enable core cryptographic identity frameworks natively
create extension if not exists "uuid-ossp";

-- Initialize Primary Unique Ledger Tablespace
create table public.transaction_ledger (
    id uuid default uuid_generate_v4() primary key,
    -- Enforce absolute unique constraints at database engine level to guarantee idempotency across global CDNs
    reference_id varchar(100) not null unique, 
    total_gross_cents integer not null check (total_gross_cents > 0),
    allocation_cushion_cents integer not null check (allocation_cushion_cents >= 0),
    allocation_secondary_cents integer not null check (allocation_secondary_cents >= 0),
    allocation_banking_cents integer not null check (allocation_banking_cents >= 0),
    processed_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Indexing matrices optimized for real-time live business monitoring dashboards
create index idx_ledger_processed_at on public.transaction_ledger(processed_at);
