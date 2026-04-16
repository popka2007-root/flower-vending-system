"""Small SQLite wrapper with safe defaults for local machine persistence."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, cast


SQLiteValue = str | bytes | int | float | None
SQLiteParameters = Sequence[SQLiteValue] | Mapping[str, SQLiteValue]


class SQLiteDatabase:
    """Own a SQLite connection with WAL-friendly pragmas and serialization helpers."""

    def __init__(
        self,
        path: str | Path,
        *,
        busy_timeout_ms: int = 5_000,
        enable_wal: bool = True,
        synchronous: str = "FULL",
    ) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._connection = sqlite3.connect(str(self._path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._configure_connection(
            busy_timeout_ms=busy_timeout_ms,
            enable_wal=enable_wal,
            synchronous=synchronous,
        )

    @property
    def path(self) -> Path:
        return self._path

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def executescript(self, script: str) -> None:
        with self._lock:
            self._connection.executescript(script)
            self._connection.commit()

    def execute(self, sql: str, parameters: SQLiteParameters = ()) -> None:
        with self._lock:
            self._connection.execute(sql, parameters)
            self._connection.commit()

    def executemany(
        self,
        sql: str,
        parameter_sets: Iterable[SQLiteParameters],
    ) -> None:
        with self._lock:
            self._connection.executemany(sql, parameter_sets)
            self._connection.commit()

    def insert(self, sql: str, parameters: SQLiteParameters = ()) -> int:
        with self._lock:
            cursor = self._connection.execute(sql, parameters)
            self._connection.commit()
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite insert did not produce a row id")
            return cursor.lastrowid

    def query_one(
        self,
        sql: str,
        parameters: SQLiteParameters = (),
    ) -> sqlite3.Row | None:
        with self._lock:
            cursor = self._connection.execute(sql, parameters)
            return cast(sqlite3.Row | None, cursor.fetchone())

    def query_all(
        self,
        sql: str,
        parameters: SQLiteParameters = (),
    ) -> list[sqlite3.Row]:
        with self._lock:
            cursor = self._connection.execute(sql, parameters)
            return list(cast(Sequence[sqlite3.Row], cursor.fetchall()))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                self._connection.execute("BEGIN")
                yield self._connection
            except Exception:
                self._connection.rollback()
                raise
            else:
                self._connection.commit()

    @staticmethod
    def dumps(payload: Mapping[str, Any] | list[Any] | tuple[Any, ...] | None) -> str:
        normalized = {} if payload is None else payload
        return json.dumps(normalized, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def loads(raw_payload: str | None, *, default: Any = None) -> Any:
        if not raw_payload:
            return default
        return json.loads(raw_payload)

    def _configure_connection(
        self,
        *,
        busy_timeout_ms: int,
        enable_wal: bool,
        synchronous: str,
    ) -> None:
        pragmas = [
            ("foreign_keys", "ON"),
            ("busy_timeout", str(busy_timeout_ms)),
            ("synchronous", synchronous.upper()),
        ]
        if enable_wal:
            pragmas.append(("journal_mode", "WAL"))
        with self._lock:
            for name, value in pragmas:
                self._connection.execute(f"PRAGMA {name}={value}")
            self._connection.commit()
