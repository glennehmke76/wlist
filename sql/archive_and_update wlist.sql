DO $$
DECLARE
    v_backup_table_name TEXT;
BEGIN
    -- Generate dynamic backup table name with current date
    v_backup_table_name := 'wlist_' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD');

    -- Create backup table in backup schema
    EXECUTE FORMAT('CREATE TABLE backup.%I AS SELECT * FROM public.wlist', v_backup_table_name);
    RAISE NOTICE 'Backup created: backup.%', v_backup_table_name;

    -- 1. Truncate wlist
    TRUNCATE TABLE public.wlist;

    -- 2. Disable trigger on wlist temporarily
    ALTER TABLE public.wlist DISABLE TRIGGER ALL;

    -- 3. Insert wlist_edited to wlist
    INSERT INTO public.wlist
    SELECT * FROM public.wlist_edited;

    -- 4. Re-enable trigger
    ALTER TABLE public.wlist ENABLE TRIGGER ALL;

    -- 5. Drop wlist_edited
    DROP TABLE public.wlist_edited;

    RAISE NOTICE 'wlist update completed successfully.';

EXCEPTION
    WHEN OTHERS THEN
        -- Re-enable triggers in case of error
        ALTER TABLE public.wlist ENABLE TRIGGER ALL;
        RAISE EXCEPTION 'Error updating wlist: %', SQLERRM;
END;
$$;