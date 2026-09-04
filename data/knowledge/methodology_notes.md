# Analysis Methodology & Domain Notes

## Data Cleaning & Transformation Rules
1. **Duration Splitting**:
   - The raw `duration` column mixes minutes and seasons.
   - For `Movie` rows, duration is parsed into `duration_minutes` (integer).
   - For `TV Show` rows, duration is parsed into `duration_seasons` (integer).
   - Numeric aggregations (mean, max, min) must only target these respective typed columns.

2. **Multi-Valued Fields**:
   - `cast`, `director`, `country`, and `listed_in` frequently contain comma-delimited strings.
   - When calculating frequency counts or groupings by person, country, or genre, values must be tokenized and stripped before counting.

3. **Date Parsing**:
   - `date_added` should be converted using `pd.to_datetime(..., errors='coerce')` for monthly or yearly time-series trends.

4. **Ratings Categorization**:
   - Mature ratings include `TV-MA`, `R`, `NC-17`.
   - Family/Teen ratings include `PG`, `PG-13`, `TV-14`, `TV-PG`, `TV-G`, `TV-Y`, `TV-Y7`.
