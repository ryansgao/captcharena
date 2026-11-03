// SQLite store (Node's built-in node:sqlite). Holds verdicts and probe results only: no IP address, no full
// browser User-Agent, no cookies. Aggregates are computed here for the public page and the data exports.
import { DatabaseSync } from "node:sqlite";

const DAILY_ROW_CAP = 50_000;

export class Store {
  constructor(path) {
    this.db = new DatabaseSync(path);
    this.db.exec(`
      PRAGMA journal_mode = WAL;
      PRAGMA busy_timeout = 2000;
      CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY,
        ts INTEGER NOT NULL, day TEXT NOT NULL,
        path_class TEXT, method TEXT,
        family TEXT, operator TEXT, kind TEXT, ua_token TEXT, ua_sample TEXT,
        ip_check TEXT,
        wba_outcome TEXT, wba_category TEXT, sa_form TEXT, sa_host TEXT, sa_resolution TEXT,
        keyid TEXT, test_key INTEGER, attribution TEXT, reused INTEGER, has_nonce INTEGER, lifetime INTEGER,
        sig_count INTEGER, dir_status INTEGER, dir_ct_ok INTEGER, dir_proof_sigs INTEGER, dir_proof_valid INTEGER,
        pace TEXT, self_test INTEGER DEFAULT 0
      );
      CREATE INDEX IF NOT EXISTS obs_day ON observations(day);
      CREATE TABLE IF NOT EXISTS overflow (day TEXT PRIMARY KEY, n INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS probes (
        id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, kind TEXT NOT NULL, target TEXT NOT NULL, label TEXT,
        status INTEGER, ok INTEGER, keys INTEGER, keyids TEXT, content_type TEXT, content_type_ok INTEGER,
        proof_sigs INTEGER, proof_valid INTEGER, digest_ok INTEGER, error TEXT, extra TEXT
      );
      CREATE INDEX IF NOT EXISTS probes_target ON probes(target, ts);
    `);
    this.insertObs = this.db.prepare(`INSERT INTO observations
      (ts, day, path_class, method, family, operator, kind, ua_token, ua_sample, ip_check, wba_outcome, wba_category,
       sa_form, sa_host, sa_resolution, keyid, test_key, attribution, reused, has_nonce, lifetime, sig_count,
       dir_status, dir_ct_ok, dir_proof_sigs, dir_proof_valid, pace, self_test)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`);
    this.insertProbe = this.db.prepare(`INSERT INTO probes
      (ts, kind, target, label, status, ok, keys, keyids, content_type, content_type_ok, proof_sigs, proof_valid,
       digest_ok, error, extra) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`);
    this.countDay = this.db.prepare("SELECT COUNT(*) AS n FROM observations WHERE day = ?");
    this.dayCount = { day: null, n: 0 };
  }

  writable() {
    try {
      this.db.exec("CREATE TABLE IF NOT EXISTS health (x INTEGER); DELETE FROM health; INSERT INTO health VALUES (1);");
      return true;
    } catch {
      return false;
    }
  }

  record(o) {
    const day = new Date(o.ts * 1000).toISOString().slice(0, 10);
    if (this.dayCount.day !== day) this.dayCount = { day, n: Number(this.countDay.get(day).n) };
    if (this.dayCount.n >= DAILY_ROW_CAP) {
      this.db.prepare("INSERT INTO overflow(day, n) VALUES (?, 1) ON CONFLICT(day) DO UPDATE SET n = n + 1").run(day);
      return;
    }
    this.dayCount.n += 1;
    const b = (x) => (x === null || x === undefined ? null : x ? 1 : 0);
    this.insertObs.run(
      o.ts, day, o.pathClass, o.method, o.family, o.operator, o.kind, o.uaToken, o.uaSample, o.ipCheck,
      o.wba.outcome, o.wba.category, o.wba.signatureAgent.form, o.saHost, o.wba.directory?.resolution ?? null,
      o.wba.keyid, b(o.wba.testKey), o.wba.attribution, b(o.wba.reused), b(o.wba.hasNonce), o.wba.lifetime,
      o.wba.signatureCount, o.wba.directory?.status ?? null, b(o.wba.directory?.contentTypeOk),
      o.wba.directory?.proof?.signatures ?? null, o.wba.directory?.proof?.valid ?? null, o.pace ?? null, b(o.selfTest),
    );
  }

  recordProbe(p) {
    this.insertProbe.run(
      p.ts, p.kind, p.target, p.label ?? null, p.status ?? null, p.ok ? 1 : 0, p.keys ?? null,
      p.keyids ? JSON.stringify(p.keyids) : null, p.contentType ?? null,
      p.contentTypeOk === null || p.contentTypeOk === undefined ? null : p.contentTypeOk ? 1 : 0,
      p.proofSigs ?? null, p.proofValid ?? null, p.digestOk === null || p.digestOk === undefined ? null : p.digestOk ? 1 : 0,
      p.error ?? null, p.extra ? JSON.stringify(p.extra) : null,
    );
  }

  /** Per agent family over the window: what signs, what verifies, what complies. */
  families(sinceTs) {
    return this.db
      .prepare(
        `SELECT family, operator, kind, self_test,
          COUNT(*) AS requests,
          SUM(wba_outcome != 'unsigned') AS signed,
          SUM(wba_outcome = 'valid') AS valid,
          SUM(wba_outcome = 'invalid') AS invalid,
          SUM(wba_outcome = 'unverified') AS unverified,
          SUM(ip_check = 'match') AS ip_match,
          SUM(ip_check = 'mismatch') AS ip_mismatch,
          SUM(path_class = 'robots') AS robots_fetches,
          SUM(path_class = 'trap') AS trap_hits,
          SUM(pace = 'early') AS pace_early,
          SUM(pace = 'respected') AS pace_respected
        FROM observations WHERE ts >= ? GROUP BY family, operator, kind, self_test ORDER BY requests DESC`,
      )
      .all(sinceTs);
  }

  signers(sinceTs) {
    return this.db
      .prepare(
        `SELECT COALESCE(sa_host, '(no Signature-Agent)') AS signer, self_test,
          COUNT(*) AS requests, SUM(wba_outcome = 'valid') AS valid, SUM(wba_outcome = 'invalid') AS invalid,
          SUM(wba_outcome = 'unverified') AS unverified, COUNT(DISTINCT keyid) AS keys,
          SUM(test_key) AS test_key, SUM(has_nonce) AS with_nonce, MAX(lifetime) AS max_lifetime,
          GROUP_CONCAT(DISTINCT sa_form) AS forms, GROUP_CONCAT(DISTINCT sa_resolution) AS resolutions,
          GROUP_CONCAT(DISTINCT family) AS families
        FROM observations WHERE ts >= ? AND wba_outcome != 'unsigned' GROUP BY signer, self_test ORDER BY requests DESC`,
      )
      .all(sinceTs);
  }

  failures(sinceTs) {
    return this.db
      .prepare(
        `SELECT wba_outcome AS outcome, wba_category AS category, COUNT(*) AS n, self_test
         FROM observations WHERE ts >= ? AND wba_outcome IN ('invalid', 'unverified')
         GROUP BY outcome, category, self_test ORDER BY n DESC`,
      )
      .all(sinceTs);
  }

  latestProbes(kind) {
    return this.db
      .prepare(
        `SELECT p.* FROM probes p JOIN (SELECT target, MAX(ts) AS ts FROM probes WHERE kind = ? GROUP BY target) l
         ON p.target = l.target AND p.ts = l.ts WHERE p.kind = ? ORDER BY p.label, p.target`,
      )
      .all(kind, kind);
  }

  /** Distinct key sets a directory has served over the window (rotation evidence). */
  keySets(target, sinceTs) {
    return this.db
      .prepare("SELECT COUNT(DISTINCT keyids) AS n FROM probes WHERE kind = 'directory' AND target = ? AND ts >= ? AND ok = 1")
      .get(target, sinceTs).n;
  }

  monthly() {
    return this.db
      .prepare(
        `SELECT substr(day, 1, 7) AS month, family, operator, kind, self_test, COUNT(*) AS requests,
          SUM(wba_outcome != 'unsigned') AS signed, SUM(wba_outcome = 'valid') AS valid,
          SUM(wba_outcome = 'invalid') AS invalid, SUM(wba_outcome = 'unverified') AS unverified,
          SUM(ip_check = 'match') AS ip_match, SUM(ip_check = 'mismatch') AS ip_mismatch,
          SUM(path_class = 'robots') AS robots_fetches, SUM(path_class = 'trap') AS trap_hits,
          SUM(pace = 'early') AS pace_early, SUM(pace = 'respected') AS pace_respected
        FROM observations GROUP BY month, family, operator, kind, self_test ORDER BY month, requests DESC`,
      )
      .all();
  }

  totals(sinceTs) {
    return this.db
      .prepare(
        `SELECT COUNT(*) AS requests, SUM(wba_outcome != 'unsigned') AS signed, SUM(wba_outcome = 'valid') AS valid,
          MIN(ts) AS first_ts, MAX(ts) AS last_ts FROM observations WHERE ts >= ? AND self_test = 0`,
      )
      .get(sinceTs);
  }

  prune(beforeTs) {
    this.db.prepare("DELETE FROM observations WHERE ts < ?").run(beforeTs);
    this.db.prepare("DELETE FROM probes WHERE ts < ?").run(beforeTs);
  }
}
