from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse

def health(request):
    database = {"status": "ok"}
    migrations = {"status": "ok"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        database = {"status": "error", "detail": exc.__class__.__name__}
    try:
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if pending:
            migrations = {"status": "pending", "count": len(pending)}
    except Exception as exc:
        migrations = {"status": "error", "detail": exc.__class__.__name__}
    status = "ok" if database["status"] == "ok" and migrations["status"] == "ok" else "degraded"
    return JsonResponse({"status": status, "service": "revision-prix-backend", "database": database, "migrations": migrations})
