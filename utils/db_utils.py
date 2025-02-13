from functools import wraps
import queue
import sqlite3
from typing import Any, List, Tuple, Union, Dict
from sqlite3 import Connection, Cursor


class DBPool:
    def __init__(self, minconn: int, maxconn: int, *args, **kwargs):
        self.minconn: int = minconn
        self.maxconn: int = maxconn
        self.args = args
        self.kwargs = kwargs
        self.pool: queue.Queue[Connection] = queue.Queue(maxsize=maxconn)
        for _ in range(minconn):
            self.pool.put(self.create_connection())

    def create_connection(self)-> Connection:
        # sqlite3 connection
        conn: Connection = sqlite3.connect('.\\files\\hr_bot.db')
        return conn

    def getconn(self) -> Connection:
        if self.pool.empty():
            if self.pool.qsize() < self.maxconn:
                self.pool.put(self.create_connection())
            else:
                raise Exception("Connection pool exhausted")
        return self.pool.get()

    def putconn(self, conn: Connection) -> None:
        self.pool.put(conn)


def db_connection(db_pool: DBPool | None):
    if db_pool is None:
        db_pool = DBPool(minconn=1, maxconn=5)

    def decorator(func: Any)-> Any:
        @wraps(wrapped=func)
        def wrapper(*args:Any, **kwargs:Any) -> Any:
            
            connection = None
            cursor = None
            try:
                connection: Connection = db_pool.getconn()
                print('Connected to PostgreSQL database successfully.')
                cursor: Cursor = connection.cursor()
                result: Any = func(*args, cursor=cursor, **kwargs)
                connection.commit()
                return result
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                if connection:
                    connection.rollback()
                raise e
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    db_pool.putconn(connection)

        return wrapper
    return decorator


db_pool = DBPool(minconn=1, maxconn=5)

@db_connection(db_pool)
def execute_query(query: str, args: Tuple[Any], cursor: Cursor) -> List[Union[Dict[Any, Any], Tuple[Any]]]:
    cursor.execute(query, args)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# print(execute_query("SELECT * FROM paysheet WHERE Code = ?", args=("210",)))