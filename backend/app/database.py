
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "qbr.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS qbr_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                quarter TEXT NOT NULL,
                year INTEGER NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(customer_name, quarter, year)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS kpi_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                period TEXT NOT NULL
                    CHECK(period IN ('previous', 'current')),
                filename TEXT NOT NULL,
                records_json TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(case_id, period),
                FOREIGN KEY(case_id)
                    REFERENCES qbr_cases(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id)
                    REFERENCES qbr_cases(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                source_location TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(document_id)
                    REFERENCES evidence_documents(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS
            evidence_fts USING fts5(
                content,
                content='evidence_chunks',
                content_rowid='id'
            )
            """
        )

        connection.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS evidence_chunks_ai
            AFTER INSERT ON evidence_chunks BEGIN
                INSERT INTO evidence_fts(rowid, content)
                VALUES (new.id, new.content);
            END;

            CREATE TRIGGER IF NOT EXISTS evidence_chunks_ad
            AFTER DELETE ON evidence_chunks BEGIN
                INSERT INTO evidence_fts(
                    evidence_fts, rowid, content
                )
                VALUES ('delete', old.id, old.content);
            END;

            CREATE TRIGGER IF NOT EXISTS evidence_chunks_au
            AFTER UPDATE ON evidence_chunks BEGIN
                INSERT INTO evidence_fts(
                    evidence_fts, rowid, content
                )
                VALUES ('delete', old.id, old.content);

                INSERT INTO evidence_fts(rowid, content)
                VALUES (new.id, new.content);
            END;
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS commitments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                owner TEXT NOT NULL,
                due_date TEXT,
                status TEXT NOT NULL
                    CHECK(status IN (
                        'open', 'in_progress',
                        'completed', 'blocked'
                    )),
                source_document_id INTEGER,
                source_location TEXT,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id)
                    REFERENCES qbr_cases(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(source_document_id)
                    REFERENCES evidence_documents(id)
                    ON DELETE SET NULL
            )
            """
        )

        connection.commit()
