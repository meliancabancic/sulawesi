import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "sulawesi.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS earthquakes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT    NOT NULL,          -- 'cmt' | 'usgs'
            lon         REAL    NOT NULL,
            lat         REAL    NOT NULL,
            depth       REAL    NOT NULL,
            magnitude   REAL    NOT NULL,
            year        INTEGER NOT NULL,
            fault_type  TEXT    NOT NULL DEFAULT 'O',
            strike1     INTEGER,
            dip1        INTEGER,
            rake1       INTEGER,
            strike2     INTEGER,
            dip2        INTEGER,
            rake2       INTEGER,
            label       TEXT    DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_eq_mag   ON earthquakes(magnitude);
        CREATE INDEX IF NOT EXISTS idx_eq_year  ON earthquakes(year);
        CREATE INDEX IF NOT EXISTS idx_eq_depth ON earthquakes(depth);
        CREATE INDEX IF NOT EXISTS idx_eq_ft    ON earthquakes(fault_type);
        CREATE INDEX IF NOT EXISTS idx_eq_src   ON earthquakes(source);

        CREATE TABLE IF NOT EXISTS annotations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            lon        REAL NOT NULL,
            lat        REAL NOT NULL,
            text       TEXT NOT NULL,
            username   TEXT NOT NULL DEFAULT 'anónimo',
            color      TEXT DEFAULT '#ffdd2c',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS geo_features (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_id TEXT,
            source       TEXT NOT NULL,
            layer_type   TEXT NOT NULL,
            name         TEXT,
            geometry     TEXT NOT NULL,
            properties   TEXT,
            confidence   REAL DEFAULT 1.0,
            year         INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_gf_source    ON geo_features(source);
        CREATE INDEX IF NOT EXISTS idx_gf_layertype ON geo_features(layer_type);
        CREATE INDEX IF NOT EXISTS idx_gf_canonical ON geo_features(canonical_id);

        CREATE TABLE IF NOT EXISTS canonical_structures (
            id           TEXT PRIMARY KEY,
            layer_type   TEXT NOT NULL,
            name         TEXT,
            merged_geom  TEXT,
            uncert_geom  TEXT,
            source_count INTEGER DEFAULT 0,
            sources      TEXT,
            properties   TEXT,
            updated_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_cs_layertype ON canonical_structures(layer_type);

        CREATE TABLE IF NOT EXISTS match_proposals (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_a_id INTEGER REFERENCES geo_features(id),
            feature_b_id INTEGER REFERENCES geo_features(id),
            similarity   REAL,
            status       TEXT DEFAULT 'pending',
            canonical_id TEXT,
            notes        TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_mp_status ON match_proposals(status);
    """)
    conn.commit()
    conn.close()
