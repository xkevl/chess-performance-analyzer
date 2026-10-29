-- Chess Performance Analyzer
-- Database: chess_analytics
-- SQL dialect: MySQL 8+

-- =====================================================
-- 1. Overall performance
-- =====================================================

SELECT
    COUNT(*) AS total_games,
    SUM(result = 'win') AS wins,
    SUM(result = 'loss') AS losses,
    SUM(result = 'draw') AS draws,
    ROUND(
        100.0 * (SUM(result = 'win') + 0.5 * SUM(result = 'draw'))
        / COUNT(*),
        2
    ) AS score_percentage
FROM chess_analytics.games
WHERE time_class = 'rapid';


-- =====================================================
-- 2. Performance by color
-- =====================================================

SELECT
    color,
    COUNT(*) AS games,
    SUM(result = 'win') AS wins,
    SUM(result = 'loss') AS losses,
    SUM(result = 'draw') AS draws,
    ROUND(
        100.0 * (SUM(result = 'win') + 0.5 * SUM(result = 'draw'))
        / COUNT(*),
        2
    ) AS score_percentage
FROM chess_analytics.games
WHERE time_class = 'rapid'
GROUP BY color
ORDER BY color;


-- =====================================================
-- 3. Performance by opening and color
-- Only include openings played at least 10 times.
-- Score percentage counts a draw as half a point.
-- =====================================================

SELECT
    color,
    opening,
    COUNT(*) AS games,
    SUM(result = 'win') AS wins,
    SUM(result = 'loss') AS losses,
    SUM(result = 'draw') AS draws,
    ROUND(
        100.0 * (SUM(result = 'win') + 0.5 * SUM(result = 'draw'))
        / COUNT(*),
        2
    ) AS score_percentage,
    ROUND(AVG(player_rating - opponent_rating), 0) AS avg_rating_difference
FROM chess_analytics.games
WHERE time_class = 'rapid'
  AND opening IS NOT NULL
  AND TRIM(opening) <> ''
GROUP BY color, opening
HAVING COUNT(*) >= 10
ORDER BY score_percentage DESC, games DESC;


-- =====================================================
-- 4. Monthly Rapid performance view
-- =====================================================

CREATE OR REPLACE VIEW chess_analytics.monthly_rapid_performance AS
SELECT
    DATE_FORMAT(game_date, '%Y-%m') AS month,
    COUNT(*) AS games,
    SUM(result = 'win') AS wins,
    SUM(result = 'loss') AS losses,
    SUM(result = 'draw') AS draws,
    ROUND(
        100.0 * (
            SUM(result = 'win') + 0.5 * SUM(result = 'draw')
        ) / COUNT(*),
        2
    ) AS score_percentage,
    ROUND(AVG(player_rating), 0) AS average_rating
FROM chess_analytics.games
WHERE time_class = 'rapid'
GROUP BY DATE_FORMAT(game_date, '%Y-%m');


-- Preview monthly results for Tableau export
SELECT *
FROM chess_analytics.monthly_rapid_performance
ORDER BY month;
