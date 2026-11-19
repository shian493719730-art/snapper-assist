CREATE TABLE policy (
 id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL DEFAULT 0,
 budget INTEGER NOT NULL DEFAULT 0, used INTEGER NOT NULL DEFAULT 0,
 request_limit INTEGER NOT NULL DEFAULT 0, requests INTEGER NOT NULL DEFAULT 0
);
--> statement-breakpoint
CREATE TABLE invites (
 id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, label TEXT NOT NULL,
 expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0,
 device_hash TEXT, budget INTEGER NOT NULL DEFAULT 0, used INTEGER NOT NULL DEFAULT 0,
 request_limit INTEGER NOT NULL DEFAULT 0, requests INTEGER NOT NULL DEFAULT 0,
 daily_limit INTEGER NOT NULL DEFAULT 0
);
--> statement-breakpoint
CREATE TABLE runs (
 id TEXT PRIMARY KEY, invite_id TEXT NOT NULL REFERENCES invites(id), input_hash TEXT NOT NULL,
 created INTEGER NOT NULL, day TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('pending','done','uncertain')),
 reserved INTEGER NOT NULL CHECK(reserved>0), charged INTEGER NOT NULL DEFAULT 0,
 input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0
);
--> statement-breakpoint
CREATE INDEX runs_daily ON runs(invite_id,day);
--> statement-breakpoint
CREATE TRIGGER reserve_budget BEFORE INSERT ON runs BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM policy WHERE id=1 AND enabled=1
  AND budget>0 AND used+NEW.reserved<=budget AND requests<request_limit)
  THEN RAISE(ABORT,'global_limit') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM invites WHERE id=NEW.invite_id AND revoked=0
  AND expires>NEW.created AND budget>0 AND used+NEW.reserved<=budget
  AND requests<request_limit AND daily_limit>(SELECT COUNT(*) FROM runs WHERE invite_id=NEW.invite_id AND day=NEW.day))
  THEN RAISE(ABORT,'invite_limit') END;
END;
--> statement-breakpoint
CREATE TRIGGER take_budget AFTER INSERT ON runs BEGIN
 UPDATE policy SET used=used+NEW.reserved, requests=requests+1 WHERE id=1;
 UPDATE invites SET used=used+NEW.reserved, requests=requests+1 WHERE id=NEW.invite_id;
END;
--> statement-breakpoint
CREATE TRIGGER settle_budget BEFORE UPDATE OF state ON runs WHEN OLD.state='pending' AND NEW.state<>'pending' BEGIN
 SELECT CASE WHEN NEW.charged<0 OR NEW.charged>OLD.reserved THEN RAISE(ABORT,'invalid_settlement') END;
END;
--> statement-breakpoint
CREATE TRIGGER refund_unused AFTER UPDATE OF state ON runs WHEN OLD.state='pending' AND NEW.state<>'pending' BEGIN
 UPDATE policy SET used=used-(OLD.reserved-NEW.charged) WHERE id=1;
 UPDATE invites SET used=used-(OLD.reserved-NEW.charged) WHERE id=OLD.invite_id;
END;

CREATE TABLE provider (id INTEGER PRIMARY KEY CHECK(id=1),base_url TEXT NOT NULL,model TEXT NOT NULL,sealed TEXT NOT NULL);
