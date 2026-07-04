create function update_is_core() returns trigger
  language plpgsql
as
$$
BEGIN
    -- Set is_core based on population value
    IF NEW.population IS NULL
       OR (NEW.population NOT LIKE '%Extinct%'
           AND NEW.population <> 'Failed introduction') THEN
        NEW.is_core := 1;
    ELSE
        NEW.is_core := NULL;
    END IF;

    RETURN NEW;
END;
$$;

alter function update_is_core() owner to glennehmke;

