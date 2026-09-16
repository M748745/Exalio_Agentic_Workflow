"""
Chat-with-Data Agent (AI Planet Feature)
Natural language querying that translates to SQL queries and generates charts/analytics

Features:
- Natural language to SQL translation
- Multi-database support (MySQL, PostgreSQL, SQLite, etc.)
- Auto-generate visualizations (charts, graphs)
- Query validation and security
- Result caching
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass
import sqlparse
import re

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a natural language query"""
    sql_query: str
    data: pd.DataFrame
    visualization: Optional[Dict[str, Any]] = None
    explanation: str = ""
    query_type: str = ""  # select, aggregate, join, etc.
    execution_time_ms: float = 0.0


class ChatWithDataAgent:
    """
    Chat-with-Data Agent
    Translates natural language to SQL and generates visualizations
    """

    def __init__(self, llm_provider, db_connector):
        self.llm_provider = llm_provider
        self.db_connector = db_connector
        self._schema_cache = None

    async def query(
        self,
        natural_language_query: str,
        auto_visualize: bool = True,
        explain: bool = True
    ) -> QueryResult:
        """
        Process natural language query

        Args:
            natural_language_query: User's question in natural language
            auto_visualize: Automatically generate charts
            explain: Generate explanation of the query

        Returns:
            QueryResult with SQL, data, and visualization
        """
        logger.info(f"Chat-with-Data query: {natural_language_query}")

        # 1. Get database schema
        schema = await self._get_schema()

        # 2. Translate NL to SQL
        sql_query = await self._nl_to_sql(natural_language_query, schema)

        # 3. Validate SQL
        is_valid, error = self._validate_sql(sql_query)
        if not is_valid:
            raise ValueError(f"Invalid SQL generated: {error}")

        # 4. Execute query
        import time
        start_time = time.time()
        df = await self.db_connector.execute_query(sql_query)
        execution_time_ms = (time.time() - start_time) * 1000

        # 5. Determine query type
        query_type = self._classify_query(sql_query)

        # 6. Generate visualization
        visualization = None
        if auto_visualize and not df.empty:
            visualization = await self._auto_visualize(df, natural_language_query, query_type)

        # 7. Generate explanation
        explanation = ""
        if explain:
            explanation = await self._explain_query(natural_language_query, sql_query, df)

        return QueryResult(
            sql_query=sql_query,
            data=df,
            visualization=visualization,
            explanation=explanation,
            query_type=query_type,
            execution_time_ms=execution_time_ms
        )

    async def _get_schema(self) -> Dict[str, Any]:
        """Get database schema with caching"""
        if self._schema_cache:
            return self._schema_cache

        schema = await self.db_connector.get_schema()
        self._schema_cache = schema
        return schema

    async def _nl_to_sql(self, nl_query: str, schema: Dict[str, Any]) -> str:
        """Translate natural language to SQL using LLM"""

        # Format schema for prompt
        schema_str = self._format_schema(schema)

        prompt = f"""You are an expert SQL query generator. Convert the natural language question to a SQL query.

Database Schema:
{schema_str}

Natural Language Question: {nl_query}

Requirements:
1. Generate ONLY the SQL query, no explanations
2. Use proper SQL syntax
3. Use table and column names exactly as shown in schema
4. Use appropriate JOINs, WHERE clauses, GROUP BY, ORDER BY as needed
5. For aggregations, use COUNT, SUM, AVG, MIN, MAX appropriately
6. Limit results to 1000 rows for safety
7. NEVER use DELETE, UPDATE, INSERT, DROP, or other destructive operations

SQL Query:"""

        response = await self.llm_provider.query(
            prompt=prompt,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=500
        )

        # Extract SQL from response
        sql_query = self._extract_sql(response)

        return sql_query

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """Format schema for LLM prompt"""
        schema_lines = []

        for table_name, table_info in schema.items():
            columns = table_info.get('columns', [])
            column_list = ", ".join([f"{col['name']} ({col['type']})" for col in columns])
            schema_lines.append(f"Table: {table_name}")
            schema_lines.append(f"  Columns: {column_list}")

            # Add sample data if available
            if 'sample_data' in table_info:
                schema_lines.append(f"  Sample: {table_info['sample_data']}")

        return "\n".join(schema_lines)

    def _extract_sql(self, llm_response: str) -> str:
        """Extract SQL query from LLM response"""
        # Remove markdown code blocks
        sql = llm_response.strip()
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)

        # Extract first SQL statement
        sql = sql.strip().split(';')[0]

        return sql

    def _validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL query for safety and correctness"""

        # 1. Parse SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "Empty SQL query"
        except Exception as e:
            return False, f"SQL parsing error: {str(e)}"

        # 2. Check for destructive operations
        sql_upper = sql.upper()
        destructive_keywords = ['DELETE', 'DROP', 'TRUNCATE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']

        for keyword in destructive_keywords:
            if keyword in sql_upper:
                return False, f"Destructive operation not allowed: {keyword}"

        # 3. Check for SELECT statement
        if not sql_upper.strip().startswith('SELECT'):
            return False, "Only SELECT queries are allowed"

        return True, None

    def _classify_query(self, sql: str) -> str:
        """Classify SQL query type"""
        sql_upper = sql.upper()

        if 'JOIN' in sql_upper:
            return 'join'
        elif any(agg in sql_upper for agg in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']):
            if 'GROUP BY' in sql_upper:
                return 'group_aggregate'
            else:
                return 'aggregate'
        elif 'WHERE' in sql_upper:
            return 'filter'
        else:
            return 'select'

    async def _auto_visualize(
        self,
        df: pd.DataFrame,
        nl_query: str,
        query_type: str
    ) -> Dict[str, Any]:
        """Auto-generate visualization based on data and query"""

        # Determine best chart type
        chart_type = self._suggest_chart_type(df, query_type)

        # Generate chart
        fig = self._create_chart(df, chart_type)

        return {
            'type': chart_type,
            'plotly_json': fig.to_json() if fig else None,
            'html': fig.to_html() if fig else None
        }

    def _suggest_chart_type(self, df: pd.DataFrame, query_type: str) -> str:
        """Suggest best chart type based on data shape"""

        num_cols = len(df.columns)
        num_rows = len(df)

        # Single numeric value
        if num_rows == 1 and num_cols == 1:
            return 'metric'

        # Time series detection
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            return 'line'

        # Categorical + Numeric
        if num_cols == 2:
            col1_type = df.iloc[:, 0].dtype
            col2_type = df.iloc[:, 1].dtype

            # Categorical x Numeric
            if col1_type == 'object' and pd.api.types.is_numeric_dtype(col2_type):
                if num_rows <= 10:
                    return 'bar'
                else:
                    return 'horizontal_bar'

        # Aggregations
        if query_type == 'group_aggregate':
            return 'bar'

        # Default to table
        return 'table'

    def _create_chart(self, df: pd.DataFrame, chart_type: str):
        """Create Plotly chart"""

        if chart_type == 'metric':
            # Single metric display
            value = df.iloc[0, 0]
            fig = go.Figure(go.Indicator(
                mode="number",
                value=value,
                title={'text': df.columns[0]}
            ))
            return fig

        elif chart_type == 'bar':
            # Bar chart
            fig = px.bar(
                df,
                x=df.columns[0],
                y=df.columns[1] if len(df.columns) > 1 else None,
                title=f"{df.columns[1]} by {df.columns[0]}" if len(df.columns) > 1 else df.columns[0]
            )
            return fig

        elif chart_type == 'horizontal_bar':
            # Horizontal bar chart
            fig = px.bar(
                df,
                y=df.columns[0],
                x=df.columns[1] if len(df.columns) > 1 else None,
                orientation='h',
                title=f"{df.columns[1]} by {df.columns[0]}" if len(df.columns) > 1 else df.columns[0]
            )
            return fig

        elif chart_type == 'line':
            # Line chart
            fig = px.line(
                df,
                x=df.columns[0],
                y=df.columns[1] if len(df.columns) > 1 else None,
                title=f"{df.columns[1]} over {df.columns[0]}" if len(df.columns) > 1 else df.columns[0]
            )
            return fig

        elif chart_type == 'pie':
            # Pie chart
            fig = px.pie(
                df,
                names=df.columns[0],
                values=df.columns[1] if len(df.columns) > 1 else None,
                title=f"Distribution of {df.columns[1]}" if len(df.columns) > 1 else df.columns[0]
            )
            return fig

        else:
            # Default: no chart
            return None

    async def _explain_query(
        self,
        nl_query: str,
        sql_query: str,
        df: pd.DataFrame
    ) -> str:
        """Generate human-readable explanation of the query and results"""

        prompt = f"""Explain this SQL query in simple terms.

Original Question: {nl_query}

SQL Query:
{sql_query}

Result Summary:
- Rows returned: {len(df)}
- Columns: {', '.join(df.columns.tolist())}

Provide a concise 2-3 sentence explanation of:
1. What data was retrieved
2. How the query worked
3. What the results show

Explanation:"""

        explanation = await self.llm_provider.query(
            prompt=prompt,
            temperature=0.3,
            max_tokens=200
        )

        return explanation.strip()

    async def suggest_followup_questions(
        self,
        original_query: str,
        result: QueryResult
    ) -> List[str]:
        """Suggest follow-up questions based on results"""

        prompt = f"""Based on this data query and results, suggest 3 relevant follow-up questions.

Original Question: {original_query}

SQL Query: {result.sql_query}

Result Summary:
- Rows: {len(result.data)}
- Columns: {', '.join(result.data.columns.tolist())}

Generate 3 specific follow-up questions that would provide additional insights.

Follow-up Questions:
1.
2.
3."""

        response = await self.llm_provider.query(
            prompt=prompt,
            temperature=0.5,
            max_tokens=200
        )

        # Extract questions
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                question = re.sub(r'^\d+\.?\s*', '', line)
                question = re.sub(r'^-\s*', '', question)
                if question:
                    questions.append(question)

        return questions[:3]
