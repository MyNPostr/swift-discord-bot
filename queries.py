GET_PLAYER_BY_NAME = """
SELECT
  ps.uuid,
  ps.name,
  ps.team,
  ps.kills,
  ps.updated_at,
  gd.display_raw
FROM player_stats ps
LEFT JOIN (
  SELECT g.name AS team,
         SUBSTRING(g.permission, LENGTH('displayname.') + 1) AS display_raw
  FROM luckperms_group_permissions g
  JOIN (
      SELECT name, MAX(id) AS mid
      FROM luckperms_group_permissions
      WHERE permission LIKE 'displayname.%%'
      GROUP BY name
  ) m ON m.name = g.name AND m.mid = g.id
) gd ON gd.team = ps.team
WHERE LOWER(ps.name) = LOWER(%s)
LIMIT 1;
"""

GET_TEAM_INFO = """
SELECT
  ps.team,
  gd.display_raw,
  COUNT(*) AS members,
  COALESCE(SUM(ps.kills), 0) AS kills
FROM player_stats ps
LEFT JOIN (
  SELECT g.name AS team,
         SUBSTRING(g.permission, LENGTH('displayname.') + 1) AS display_raw
  FROM luckperms_group_permissions g
  JOIN (
      SELECT name, MAX(id) AS mid
      FROM luckperms_group_permissions
      WHERE permission LIKE 'displayname.%%'
      GROUP BY name
  ) m ON m.name = g.name AND m.mid = g.id
) gd ON gd.team = ps.team
WHERE ps.team = %s
GROUP BY ps.team, gd.display_raw
LIMIT 1;
"""

GET_TEAM_MEMBERS = """
SELECT
  name,
  kills,
  updated_at
FROM player_stats
WHERE team = %s
ORDER BY kills DESC, name ASC
LIMIT 25;
"""

TOP_TEAMS_BY_KILLS = """
SELECT
  ps.team,
  gd.display_raw,
  COUNT(*) AS members,
  COALESCE(SUM(ps.kills), 0) AS kills
FROM player_stats ps
LEFT JOIN (
  SELECT g.name AS team,
         SUBSTRING(g.permission, LENGTH('displayname.') + 1) AS display_raw
  FROM luckperms_group_permissions g
  JOIN (
      SELECT name, MAX(id) AS mid
      FROM luckperms_group_permissions
      WHERE permission LIKE 'displayname.%%'
      GROUP BY name
  ) m ON m.name = g.name AND m.mid = g.id
) gd ON gd.team = ps.team
WHERE ps.team IS NOT NULL AND ps.team <> ''
GROUP BY ps.team, gd.display_raw
ORDER BY kills DESC, members DESC, ps.team ASC
LIMIT %s;
"""

TOP_PLAYERS_BY_KILLS = """
SELECT
  ps.name,
  ps.team,
  ps.kills,
  ps.updated_at,
  gd.display_raw
FROM player_stats ps
LEFT JOIN (
  SELECT g.name AS team,
         SUBSTRING(g.permission, LENGTH('displayname.') + 1) AS display_raw
  FROM luckperms_group_permissions g
  JOIN (
      SELECT name, MAX(id) AS mid
      FROM luckperms_group_permissions
      WHERE permission LIKE 'displayname.%%'
      GROUP BY name
  ) m ON m.name = g.name AND m.mid = g.id
) gd ON gd.team = ps.team
ORDER BY ps.kills DESC, ps.name ASC
LIMIT %s;
"""
