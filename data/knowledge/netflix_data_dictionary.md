# Netflix Movies and TV Shows Data Dictionary

## Overview
This dataset consists of listings of all the movies and tv shows available on Netflix, along with details such as cast, directors, ratings, release year, duration, etc.

## Column Descriptions

| Column | Type | Description | Notes |
|---|---|---|---|
| `show_id` | String | Unique identifier for each title | Formatted as `s1`, `s2`, etc. |
| `type` | String | Content category | Values are either `Movie` or `TV Show`. |
| `title` | String | Title of the Movie or TV Show | Clean text title. |
| `director` | String | Director(s) of the content | May contain comma-separated multiple directors, or missing values. |
| `cast` | String | Featured actors and actresses | Comma-separated list of cast members; requires splitting for individual actor counts. |
| `country` | String | Country or countries of production | Can be comma-separated if co-produced across multiple countries. |
| `date_added` | Date String | Date the title was added to Netflix | Format: `Month DD, YYYY` (e.g. `September 25, 2021`). |
| `release_year` | Integer | Original release year of the title | 4-digit year. |
| `rating` | String | Target audience / age rating | Examples: `PG-13`, `TV-MA`, `R`, `TV-14`, `TV-PG`. |
| `duration` | String | Raw duration string | Examples: `90 min`, `2 Seasons`. |
| `duration_minutes` | Integer | Extracted numeric duration in minutes | Derived column populated only for `Movie` entries. |
| `duration_seasons` | Integer | Extracted numeric season count | Derived column populated only for `TV Show` entries. |
| `listed_in` | String | Genre categories | Comma-separated genres (e.g., `Documentaries`, `International TV Shows`). |
| `description` | String | Summary synopsis | Free-text overview of the plot or premise. |
