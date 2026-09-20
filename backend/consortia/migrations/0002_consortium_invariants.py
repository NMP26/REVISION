from django.db import migrations


FORWARD_SQL = """
CREATE OR REPLACE FUNCTION consortia_check_invariants(p_consortium_id uuid)
RETURNS void
LANGUAGE plpgsql
AS $function$
DECLARE
    active_count integer;
    mandataire_count integer;
    share_count integer;
    share_total numeric;
BEGIN
    SELECT count(*), count(*) FILTER (WHERE role = 'MANDATAIRE'), count(*) FILTER (WHERE share_percent IS NOT NULL), COALESCE(sum(share_percent), 0)
    INTO active_count, mandataire_count, share_count, share_total
    FROM consortia_consortiummember
    WHERE consortium_id = p_consortium_id AND active = TRUE;

    IF active_count < 2 THEN
        RAISE EXCEPTION 'A consortium must have at least two active members';
    END IF;
    IF mandataire_count <> 1 THEN
        RAISE EXCEPTION 'A consortium must have exactly one active mandataire';
    END IF;
    IF share_count = active_count AND share_total <> 100.00 THEN
        RAISE EXCEPTION 'All populated consortium shares must total exactly 100.00';
    END IF;
END;
$function$;

CREATE OR REPLACE FUNCTION consortia_check_invariants_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF TG_TABLE_NAME = 'consortia_consortium' THEN
        PERFORM consortia_check_invariants(NEW.id);
    ELSIF TG_OP = 'UPDATE' AND OLD.consortium_id IS DISTINCT FROM NEW.consortium_id THEN
        PERFORM consortia_check_invariants(OLD.consortium_id);
        PERFORM consortia_check_invariants(NEW.consortium_id);
    ELSE
        PERFORM consortia_check_invariants(COALESCE(NEW.consortium_id, OLD.consortium_id));
    END IF;
    RETURN NULL;
END;
$function$;

CREATE CONSTRAINT TRIGGER consortia_member_invariants
AFTER INSERT OR UPDATE OR DELETE ON consortia_consortiummember
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION consortia_check_invariants_trigger();

CREATE CONSTRAINT TRIGGER consortia_group_invariants
AFTER INSERT OR UPDATE ON consortia_consortium
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION consortia_check_invariants_trigger();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS consortia_group_invariants ON consortia_consortium;
DROP TRIGGER IF EXISTS consortia_member_invariants ON consortia_consortiummember;
DROP FUNCTION IF EXISTS consortia_check_invariants_trigger();
DROP FUNCTION IF EXISTS consortia_check_invariants(uuid);
"""


class Migration(migrations.Migration):
    dependencies = [("consortia", "0001_initial")]
    operations = [migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)]
