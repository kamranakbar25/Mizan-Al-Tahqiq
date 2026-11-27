"""Read-only Phase 1 schema and migration inventory for Mizan Al-Tahqiq.
Run from the Django project root with the project's configured virtualenv:
    python tools/phase1_readonly_audit.py
This script does not run migrations, save models, or alter database objects.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from datetime import datetime, timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.executor import MigrationExecutor
from django.apps import apps

out_dir = Path("_project_admin/reports")
out_dir.mkdir(parents=True, exist_ok=True)
report = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "evidence_type": "live_read_only_django_database_introspection",
    "database": {},
    "tables": [],
    "migration": {},
    "models": [],
    "warnings": [
        "Read-only inventory only; no migration or schema changes were performed.",
        "Review output before sharing; it contains schema metadata, not credentials or row contents."
    ],
}

with connection.cursor() as cursor:
    cursor.execute("SELECT current_database(), current_user, current_schema(), version()")
    db_name, db_user, db_schema, db_version = cursor.fetchone()
    report["database"] = {
        "vendor": connection.vendor,
        "name": db_name,
        "user": db_user,
        "schema": db_schema,
        "server_version": db_version,
    }

introspection = connection.introspection
with connection.cursor() as cursor:
    table_names = sorted(introspection.table_names(cursor))
    for table in table_names:
        description = introspection.get_table_description(cursor, table)
        constraints = introspection.get_constraints(cursor, table)
        report["tables"].append({
            "name": table,
            "columns": [
                {
                    "name": col.name,
                    "type_code": str(col.type_code),
                    "null_ok": col.null_ok,
                    "default": str(col.default) if col.default is not None else None,
                }
                for col in description
            ],
            "constraints": [
                {
                    "name": name,
                    "columns": value.get("columns", []),
                    "primary_key": bool(value.get("primary_key")),
                    "unique": bool(value.get("unique")),
                    "foreign_key": value.get("foreign_key"),
                    "check": bool(value.get("check")),
                    "index": bool(value.get("index")),
                }
                for name, value in sorted(constraints.items())
            ],
        })

loader = MigrationLoader(connection, ignore_no_migrations=True)
executor = MigrationExecutor(connection)
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name, applied FROM django_migrations ORDER BY app, name")
    applied = [
        {"app": app, "name": name, "applied_at": applied_at.isoformat() if applied_at else None}
        for app, name, applied_at in cursor.fetchall()
    ]
report["migration"] = {
    "applied": applied,
    "leaf_nodes": [list(x) for x in sorted(loader.graph.leaf_nodes())],
    "disk_migrations": [list(x) for x in sorted(loader.disk_migrations)],
    "plan_from_leaves": [
        {"app": migration.app_label, "name": migration.name, "backwards": backwards}
        for migration, backwards in executor.migration_plan(loader.graph.leaf_nodes())
    ],
}

for model in apps.get_models():
    report["models"].append({
        "app_label": model._meta.app_label,
        "model": model.__name__,
        "db_table": model._meta.db_table,
        "fields": [
            {
                "name": field.name,
                "column": getattr(field, "column", None),
                "type": field.get_internal_type(),
                "null": getattr(field, "null", None),
                "primary_key": bool(getattr(field, "primary_key", False)),
                "related_model": str(field.related_model._meta.label) if getattr(field, "related_model", None) else None,
            }
            for field in model._meta.get_fields()
            if getattr(field, "concrete", False)
        ],
    })

path = out_dir / f"phase1_readonly_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Read-only Phase 1 audit written: {path}")
print(f"Database: {report['database']['name']} ({report['database']['vendor']})")
print(f"Tables: {len(report['tables'])}; applied migrations: {len(report['migration']['applied'])}; Django models: {len(report['models'])}")
print("No schema or data changes were made.")
