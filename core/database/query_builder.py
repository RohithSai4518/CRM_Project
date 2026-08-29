"""
CRM System - Fluent SQL Query Builder
Zero external ORM dependencies
"""

from typing import List, Dict, Any, Tuple, Optional, Union
from core.database.connection import DB


class QueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._select_fields: List[str] = ["*"]
        self._where_clauses: List[str] = []
        self._where_params: List[Any] = []
        self._order_by: List[str] = []
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._joins: List[str] = []

    def select(self, *fields: str) -> "QueryBuilder":
        if fields:
            self._select_fields = list(fields)
        return self

    def where(self, column: str, operator: str, value: Any) -> "QueryBuilder":
        self._where_clauses.append(f"{column} {operator} ?")
        self._where_params.append(value)
        return self

    def where_eq(self, column: str, value: Any) -> "QueryBuilder":
        return self.where(column, "=", value)

    def where_like(self, column: str, value: str) -> "QueryBuilder":
        return self.where(column, "LIKE", f"%{value}%")

    def where_in(self, column: str, values: List[Any]) -> "QueryBuilder":
        if not values:
            self._where_clauses.append("1=0")
            return self
        placeholders = ", ".join(["?"] * len(values))
        self._where_clauses.append(f"{column} IN ({placeholders})")
        self._where_params.extend(values)
        return self

    def where_is_null(self, column: str) -> "QueryBuilder":
        self._where_clauses.append(f"{column} IS NULL")
        return self

    def where_not_null(self, column: str) -> "QueryBuilder":
        self._where_clauses.append(f"{column} IS NOT NULL")
        return self

    def join(self, target_table: str, on_condition: str, join_type: str = "INNER") -> "QueryBuilder":
        self._joins.append(f"{join_type} JOIN {target_table} ON {on_condition}")
        return self

    def left_join(self, target_table: str, on_condition: str) -> "QueryBuilder":
        return self.join(target_table, on_condition, "LEFT")

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        self._order_by.append(f"{column} {direction.upper()}")
        return self

    def limit(self, count: int) -> "QueryBuilder":
        self._limit_val = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        self._offset_val = count
        return self

    def _build_select_sql(self) -> Tuple[str, Tuple[Any, ...]]:
        fields_str = ", ".join(self._select_fields)
        sql = f"SELECT {fields_str} FROM {self.table_name}"
        
        if self._joins:
            sql += " " + " ".join(self._joins)
            
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
            
        if self._order_by:
            sql += " ORDER BY " + ", ".join(self._order_by)
            
        if self._limit_val is not None:
            sql += f" LIMIT {int(self._limit_val)}"
            
        if self._offset_val is not None:
            sql += f" OFFSET {int(self._offset_val)}"
            
        return sql, tuple(self._where_params)

    def get(self) -> List[Dict[str, Any]]:
        """Execute SELECT and return all records."""
        sql, params = self._build_select_sql()
        return DB.fetch_all(sql, params)

    def first(self) -> Optional[Dict[str, Any]]:
        """Execute SELECT with limit 1 and return first record."""
        self.limit(1)
        sql, params = self._build_select_sql()
        return DB.fetch_one(sql, params)

    def count(self) -> int:
        """Count total matching records."""
        sql = f"SELECT COUNT(*) as total FROM {self.table_name}"
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        row = DB.fetch_one(sql, tuple(self._where_params))
        return int(row["total"]) if row else 0

    def insert(self, data: Dict[str, Any]) -> str:
        """Insert a row and return rowid/id."""
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        values = tuple(data.values())
        
        sql = f"INSERT INTO {self.table_name} ({col_names}) VALUES ({placeholders})"
        cursor = DB.execute(sql, values)
        return str(cursor.lastrowid)

    def update(self, data: Dict[str, Any]) -> int:
        """Update matching rows."""
        if not self._where_clauses:
            raise ValueError("Safety check: Cannot execute UPDATE without WHERE clause")
            
        set_clauses = [f"{col} = ?" for col in data.keys()]
        set_str = ", ".join(set_clauses)
        params = list(data.values()) + self._where_params
        
        sql = f"UPDATE {self.table_name} SET {set_str} WHERE " + " AND ".join(self._where_clauses)
        cursor = DB.execute(sql, tuple(params))
        return cursor.rowcount

    def delete(self) -> int:
        """Delete matching rows."""
        if not self._where_clauses:
            raise ValueError("Safety check: Cannot execute DELETE without WHERE clause")
            
        sql = f"DELETE FROM {self.table_name} WHERE " + " AND ".join(self._where_clauses)
        cursor = DB.execute(sql, tuple(self._where_params))
        return cursor.rowcount


def query(table_name: str) -> QueryBuilder:
    return QueryBuilder(table_name)
