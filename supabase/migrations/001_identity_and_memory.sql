-- Heal Companion: 账号、伴侣、会话、消息、长期记忆
-- 在 Supabase SQL Editor 执行。服务端用 service role 时会绕过 RLS，
-- 因此 API 仍必须按 JWT 的 sub 自行过滤；RLS 防止 anon key 被前端滥用。

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null default '',
  preferred_address text not null default '你',
  comfort_notes text not null default '',
  timezone text not null default 'Asia/Shanghai',
  relationship_stage text not null default 'first_meet',
  preference_tags jsonb not null default '{}'::jsonb,
  emotional_state text not null default '',
  bridge_sent_on date,
  created_at timestamptz not null default now()
);

alter table public.profiles add column if not exists bridge_sent_on date;

create table if not exists public.companions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null default 'heal',
  persona_id text not null default 'older_friend',
  created_at timestamptz not null default now(),
  unique (user_id)
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  companion_id uuid not null references public.companions (id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (user_id)
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'journal')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists messages_user_created_idx
  on public.messages (user_id, created_at);

create table if not exists public.memories (
  id text primary key,
  user_id uuid not null references auth.users (id) on delete cascade,
  kind text not null,
  summary text not null,
  details text not null default '',
  people jsonb not null default '[]'::jsonb,
  importance int not null default 3 check (importance between 1 and 5),
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  source text not null default 'chat'
);

create index if not exists memories_user_idx on public.memories (user_id);

alter table public.profiles enable row level security;
alter table public.companions enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.memories enable row level security;

drop policy if exists profiles_own on public.profiles;
create policy profiles_own on public.profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists companions_own on public.companions;
create policy companions_own on public.companions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists conversations_own on public.conversations;
create policy conversations_own on public.conversations
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists messages_own on public.messages;
create policy messages_own on public.messages
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists memories_own on public.memories;
create policy memories_own on public.memories
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id) values (new.id) on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
