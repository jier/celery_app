create table import_jobs (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    filename text not null,
    status text not null default 'queued'
        check (status in ('queued', 'processing', 'completed', 'failed')),
    total_rows integer not null default 0,
    processed_rows integer not null default 0,
    failed_rows integer not null default 0,
    created_at timestamptz not null default now()
);

create table products (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    sku text not null,
    name text not null,
    price numeric(12,2) not null,
    quantity integer not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (owner_id, sku)
);

alter table import_jobs enable row level security;
alter table products enable row level security;

create policy "Users can read their own import jobs"
    on import_jobs for select
    using (auth.uid() = owner_id);

create policy "Users can insert their own import jobs"
    on import_jobs for insert
    with check (auth.uid() = owner_id);

create policy "Users can update their own import jobs"
    on import_jobs for update
    using (auth.uid() = owner_id);

create policy "Users can read their own products"
    on products for select
    using (auth.uid() = owner_id);

create policy "Users can insert their own products"
    on products for insert
    with check (auth.uid() = owner_id);

create policy "Users can upsert their own products"
    on products for insert
    with check (auth.uid() = owner_id);

alter publication supabase_realtime add table import_jobs;
