grant usage on schema public to service_role, authenticated, anon;

grant select, insert, update, delete on public.import_jobs to service_role;
grant select, insert, update, delete on public.products to service_role;

grant select, insert, update on public.import_jobs to authenticated;
grant select, insert, update on public.products to authenticated;
