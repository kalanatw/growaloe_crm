import logging
import time
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

db_logger = logging.getLogger('db_logger')


class DatabaseQueryLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log database queries with table information
    """
    
    def process_request(self, request):
        # Reset queries at the start of each request
        connection.queries_log.clear()
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        # Log all queries made during this request
        if hasattr(request, 'start_time'):
            total_time = time.time() - request.start_time
            
            # Get the queries made during this request
            queries = connection.queries
            
            if queries:
                db_logger.info(f"Request: {request.method} {request.path}")
                db_logger.info(f"Total queries: {len(queries)}")
                db_logger.info(f"Total time: {total_time:.4f}s")
                
                for i, query in enumerate(queries, 1):
                    sql = query['sql']
                    query_time = query['time']
                    
                    # Extract table names from the query
                    tables_affected = self.extract_table_names(sql)
                    
                    db_logger.info(f"Query {i}: {query_time}s")
                    db_logger.info(f"Tables affected: {', '.join(tables_affected) if tables_affected else 'Unknown'}")
                    db_logger.info(f"SQL: {sql}")
                    db_logger.info("-" * 80)
        
        return response
    
    def extract_table_names(self, sql):
        """
        Extract table names from SQL queries
        """
        import re
        
        # Common patterns to find table names
        patterns = [
            r'FROM\s+["`]?(\w+)["`]?',
            r'JOIN\s+["`]?(\w+)["`]?',
            r'UPDATE\s+["`]?(\w+)["`]?',
            r'INSERT\s+INTO\s+["`]?(\w+)["`]?',
            r'DELETE\s+FROM\s+["`]?(\w+)["`]?',
        ]
        
        tables = set()
        sql_upper = sql.upper()
        
        for pattern in patterns:
            matches = re.findall(pattern, sql_upper, re.IGNORECASE)
            tables.update(matches)
        
        # Filter out common SQL keywords that might be matched
        keywords = {'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AS', 'AND', 'OR', 'NOT', 'NULL', 'TRUE', 'FALSE'}
        tables = {table for table in tables if table.upper() not in keywords}
        
        return list(tables)
