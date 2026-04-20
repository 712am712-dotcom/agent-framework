-- Migration 001: Multi-Brand Framework
-- Project: mnxfmzrcsbxqjswfuqeh
-- Date: 2026-04-20
--
-- What this migration does:
--   1. Create the `brands` registry table
--   2. Add `source_agent` to `signals`
--   3. Add `source_agent` and `signal_ids` to `content_jobs`
--   4. Seed known brands (mfd, ae) into the brands table
--
-- How to apply:
--   Option A — Supabase Dashboard SQL editor (recommended):
--     Paste this file into the SQL editor at
--     https://supabase.com/dashboard/project/mnxfmzrcsbxqjswfuqeh/sql/new
--     and click Run.
--
--   Option B — MCP tool:
--     Use mcp__claude_ai_Supabase__apply_migration with project_id=mnxfmzrcsbxqjswfuqeh
--
--   Option C — psql:
--     psql "$DATABASE_URL" < 001_multi_brand_framework.sql
--
-- Safe to run multiple times — all statements use IF NOT EXISTS / DO NOTHING.


-- ── 1. Create brands registry ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.brands (
    id          uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    slug        text        NOT NULL UNIQUE,
    name        text        NOT NULL,
    handle      text,
    agent_name  text,
    active      boolean     NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.brands ENABLE ROW LEVEL SECURITY;

-- Service role can do everything; anon gets nothing by default.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'brands'
          AND policyname = 'service_role_all'
    ) THEN
        CREATE POLICY service_role_all ON public.brands
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END;
$$;


-- ── 2. Add source_agent to signals ────────────────────────────────────────────

ALTER TABLE public.signals
    ADD COLUMN IF NOT EXISTS source_agent text;

COMMENT ON COLUMN public.signals.source_agent IS
    'Which intelligence agent produced this signal (e.g. ae-intel, mfd-intel)';


-- ── 3. Add source_agent and signal_ids to content_jobs ───────────────────────

ALTER TABLE public.content_jobs
    ADD COLUMN IF NOT EXISTS source_agent text;

ALTER TABLE public.content_jobs
    ADD COLUMN IF NOT EXISTS signal_ids uuid[];

COMMENT ON COLUMN public.content_jobs.source_agent IS
    'Which intelligence agent created this job (e.g. ae-intel, mfd-intel)';

COMMENT ON COLUMN public.content_jobs.signal_ids IS
    'Array of signals.id UUIDs this job was derived from — for audit/debugging';


-- ── 4. Seed known brands ──────────────────────────────────────────────────────

INSERT INTO public.brands (slug, name, handle, agent_name, active)
VALUES
    ('mfd', 'Markets For Dummies', '@marketsfordummies', 'mfd-intel', true),
    ('ae',  'Artificial Education', '@artificialeducation', 'ae-intel', true)
ON CONFLICT (slug) DO NOTHING;


-- ── Verification queries ──────────────────────────────────────────────────────
-- Run these after applying to confirm success:
--
-- SELECT * FROM brands;
-- SELECT column_name FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'signals'
--   AND column_name = 'source_agent';
-- SELECT column_name FROM information_schema.columns
--   WHERE table_schema = 'public' AND table_name = 'content_jobs'
--   AND column_name IN ('source_agent', 'signal_ids');
