from fastmcp import FastMCP
import os
import json
import sqlite3
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="ExpenseTracker")

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise
        

init_db()

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            await c.commit()
            return {"status": "ok", "id": cur.lastrowid,'message':'Expense added successfully'}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}
    
@mcp.tool()
async def update_expense(date, category, amount, subcategory=None, note=None):
    '''Update an existing expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            set_parts = ["amount = ?"]
            params = [amount]
            if note is not None:
                set_parts.append("note = ?")
                params.append(note)
            query = f"UPDATE expenses SET {', '.join(set_parts)} WHERE date = ? AND category = ?"
            params.extend([date, category])
            if subcategory is not None:
                query += " AND subcategory = ?"
                params.append(subcategory)
            cur = await c.execute(query, params)
            await c.commit()
            return {"status": "ok", "updated": cur.rowcount, "message": "Expense updated successfully"}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def delete_expense(date, category, subcategory=None):
    '''Delete an existing expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            query = "DELETE FROM expenses WHERE date = ? AND category = ?"
            params = [date, category]
            if subcategory is not None:
                query += " AND subcategory = ?"
                params.append(subcategory)
            cur = await c.execute(query, params)
            await c.commit()
            return {"status": "ok", "deleted": cur.rowcount, "message": "Expense deleted successfully"}
    except Exception as e:
        if "readonly" in str(e).lower():
            return {"status": "error", "message": "Database is in read-only mode. Check file permissions."}
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            cur = await c.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            query = (
                """
                SELECT category, SUM(amount) AS total_amount
                FROM expenses
                WHERE date BETWEEN ? AND ?
                """
            )
            params = [start_date, end_date]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " GROUP BY category ORDER BY category ASC"

            cur = await c.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}
    
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    try:
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        
        # Read fresh each time so you can edit the file without restarting
        try:
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return {"status": "error", "message": f"Could not load categories: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport='http',host='0.0.0.0',port=8000)