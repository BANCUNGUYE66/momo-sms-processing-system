from pathlib import Path
import re

def test_sql_script():
    sql_path = Path(__file__).resolve().parent.parent / "database" / "database_setup.sql"
    print(f"Testing SQL Script: {sql_path}\n")

    assert sql_path.exists(), "Error: database/database_setup.sql does not exist!"

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Check database creation
    assert "CREATE DATABASE" in sql_content, "Error: Missing CREATE DATABASE statement"
    print("  [PASS] CREATE DATABASE statement found.")

    # Check required tables
    required_tables = ["users", "transaction_categories", "user_category_preferences", "transactions", "system_logs"]
    for table in required_tables:
        pattern = rf"CREATE TABLE IF NOT EXISTS {table}"
        assert re.search(pattern, sql_content, re.IGNORECASE), f"Error: Table creation for '{table}' not found!"
        print(f"  [PASS] Table structure verified: {table}")

    # Check constraints and comments
    assert "FOREIGN KEY" in sql_content, "Error: Missing FOREIGN KEY constraints"
    print("  [PASS] Foreign key constraints verified.")

    assert "CHECK" in sql_content, "Error: Missing CHECK constraints"
    print("  [PASS] CHECK constraints verified.")

    assert "COMMENT" in sql_content, "Error: Missing column/table comments"
    print("  [PASS] Documentation comments verified.")

    # Check DML Sample Data
    assert "INSERT INTO users" in sql_content, "Error: Missing sample data for users"
    assert "INSERT INTO transactions" in sql_content, "Error: Missing sample data for transactions"
    print("  [PASS] Sample DML data insertion statements verified.")

    print("\nSUCCESS: SQL database setup script validated successfully!")

if __name__ == "__main__":
    test_sql_script()
