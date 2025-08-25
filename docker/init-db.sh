#!/bin/bash
# ==========================================
# Database Initialization Script
# Waits for SQL Server and creates database
# ==========================================

set -e

echo "🔄 Waiting for SQL Server to be ready..."

# Wait for SQL Server to be available
until /opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "${SA_PASSWORD}" -Q "SELECT 1" -C > /dev/null 2>&1; do
    echo "⏳ SQL Server is unavailable - sleeping"
    sleep 5
done

echo "✅ SQL Server is ready!"

# Create GPAlytics database if it doesn't exist
echo "🏗️  Creating GPAlytics database..."
/opt/mssql-tools18/bin/sqlcmd -S localhost -U SA -P "${SA_PASSWORD}" -C -Q "
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'GPAlytics')
BEGIN
    CREATE DATABASE GPAlytics;
    PRINT 'GPAlytics database created successfully';
END
ELSE
BEGIN
    PRINT 'GPAlytics database already exists';
END
"

echo "🎉 Database initialization completed!"