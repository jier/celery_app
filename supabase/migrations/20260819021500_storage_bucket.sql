insert into storage.buckets (id, name, public)
values ('import-files', 'import-files', false)
on conflict (id) do nothing;

create policy "Owners can read their uploaded imports"
    on storage.objects for select
    using (auth.uid()::text = (storage.foldername(name))[1]);

create policy "Authenticated users can upload imports"
    on storage.objects for insert
    with check (
        auth.uid()::text = (storage.foldername(name))[1]
        and bucket_id = 'import-files'
    );
