import os
import re
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("text_to_sql_service")

# Try importing the modern google-genai library
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class TextToSqlService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize Gemini client if API key is present
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")

    def _is_safe_select_query(self, sql_query: str) -> bool:
        """
        Validates if the generated SQL query is a safe SELECT statement
        and contains no malicious DDL/DML keywords.
        """
        clean_sql = sql_query.strip().upper()
        
        # 1. Must start with SELECT
        if not clean_sql.startswith("SELECT"):
            return False
            
        # 2. Block modifying or destructive keywords
        forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", 
            "CREATE", "REPLACE", "GRANT", "REVOKE", "EXECUTE", "UNION", "INTO"
        ]
        # Match as whole words
        for keyword in forbidden_keywords:
            if re.search(rf"\b{keyword}\b", clean_sql):
                logger.warning(f"Forbidden SQL keyword '{keyword}' detected in: {sql_query}")
                return False
                
        return True

    def _clean_sql_output(self, raw_sql: str) -> str:
        """
        Removes markdown code blocks (```sql ... ```) and leading/trailing whitespace.
        """
        cleaned = re.sub(r"```sql\s*", "", raw_sql, flags=re.IGNORECASE)
        cleaned = re.sub(r"```\s*", "", cleaned)
        return cleaned.strip()

    async def translate_to_sql(self, natural_language_query: str) -> str | None:
        """
        Translates natural language text to a PostgreSQL SELECT query using Gemini.
        Returns the SQL string or None if translation is not possible or failed.
        """
        if not self.client:
            logger.warning("Gemini API key is not configured or google-genai package is missing. Skipping Text-to-SQL.")
            return None

        prompt = f"""You are an expert PostgreSQL Text-to-SQL translator.
Given a natural language user query, you must translate it into a valid PostgreSQL SELECT query that returns hydrogen station management numbers (chrstn_mno).

Database Schema:
1. Table `hydrogen_stations` (수소충전소 기본정보):
   - `chrstn_mno` (VARCHAR(30)): 충전소 관리번호 (Primary Key)
   - `chrstn_nm` (VARCHAR(100)): 충전소명 (예: '인천공항 수소충전소')
   - `ntsl_pc` (INTEGER): 판매 가격 (예: 9900)
   - `road_nm_addr` (VARCHAR(255)): 도로명 주소 (예: '인천광역시 중구 공항로 272')
   - `lotno_addr` (VARCHAR(255)): 지번 주소 (예: '인천광역시 중구 운서동 2851')
   - `oper_yn` (CHAR(1)): 운영 여부 ('Y' / 'N')
   - `rsvt_posbl_yn` (CHAR(1)): 예약 가능 여부 ('Y' / 'N')
   - `rltm_info_yn` (CHAR(1)): 실시간 정보 제공 여부 ('Y' / 'N')

2. Table `hydrogen_station_status` (수소충전소 실시간 상태정보):
   - `status_id` (BIGSERIAL): 상태 ID (Primary Key)
   - `chrstn_mno` (VARCHAR(30)): 충전소 관리번호 (Foreign Key references hydrogen_stations.chrstn_mno)
   - `wait_vhcle_alge` (INTEGER): 대기 차량 대수 (예: 3)
   - `oper_sttus_nm` (VARCHAR(50)): 운영 상태명 (예: '영업중', '점검중', '휴무')
   - `pos_sttus_nm` (VARCHAR(50)): 충전 가능 상태명

3. Table `hydrogen_station_additional_info` (수소충전소 부대시설/추가정보):
   - `additional_info_id` (BIGSERIAL): ID (Primary Key)
   - `chrstn_mno` (VARCHAR(30)): 충전소 관리번호 (Foreign Key references hydrogen_stations.chrstn_mno)
   - `adi_info_se_nm` (VARCHAR(50)): 부대시설명 (예: '세차장', '편의점', '카페', '휴게실')

Rules:
- Respond ONLY with the executable PostgreSQL SQL query. Do not wrap it in markdown block quotes (do NOT use ```sql). Do not add any explanation, notes, or commentary.
- The SQL query must only contain a single SELECT statement. Write/DDL/DML queries are strictly forbidden.
- Always SELECT DISTINCT hs.chrstn_mno as the sole column so we can retrieve matching stations.
- Perform JOINS correctly using `chrstn_mno`.
- To avoid SQL execution failures, ensure all column names exist.

Examples:
- "인천에 있고 가격이 9900원 이하인 세차장 있는 충전소" ->
  SELECT DISTINCT hs.chrstn_mno FROM hydrogen_stations hs LEFT JOIN hydrogen_station_additional_info hai ON hs.chrstn_mno = hai.chrstn_mno WHERE (hs.road_nm_addr LIKE '%인천%' OR hs.lotno_addr LIKE '%인천%') AND hs.ntsl_pc <= 9900 AND hai.adi_info_se_nm LIKE '%세차%';

- "대기 차량이 없는 영업중인 충전소" ->
  SELECT DISTINCT hs.chrstn_mno FROM hydrogen_stations hs JOIN hydrogen_station_status hss ON hs.chrstn_mno = hss.chrstn_mno WHERE hss.wait_vhcle_alge = 0 AND hss.oper_sttus_nm = '영업중';

User Input Query: "{natural_language_query}"
Generated SQL:"""

        try:
            # Use gemini-2.5-flash as the state-of-the-art developer friendly model
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            raw_sql = response.text
            cleaned_sql = self._clean_sql_output(raw_sql)
            
            if not self._is_safe_select_query(cleaned_sql):
                logger.error(f"Generated SQL failed safety check: {cleaned_sql}")
                return None
                
            logger.info(f"Successfully generated SQL: {cleaned_sql}")
            return cleaned_sql
        except Exception as e:
            logger.error(f"Error during Text-to-SQL translation: {e}")
            return None

    async def execute_semantic_search(self, natural_language_query: str) -> list[str] | None:
        """
        Translates a natural language query into SQL, executes it, and returns the list of chrstn_mno.
        Returns None if translation fails, allowing fallback to default filters.
        """
        sql_query = await self.translate_to_sql(natural_language_query)
        if not sql_query:
            return None

        try:
            result = await self.db.execute(text(sql_query))
            rows = result.fetchall()
            matching_mno_list = [row[0] for row in rows if row[0] is not None]
            return matching_mno_list
        except Exception as e:
            logger.error(f"Failed to execute semantic search SQL query '{sql_query}': {e}")
            return None
