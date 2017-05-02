# Interesting queries

    SELECT *
    FROM buggy_action
    LEFT JOIN buggy_settitle ON (buggy_settitle.action_id = buggy_action.id)
    LEFT JOIN buggy_comment ON (buggy_comment.action_id = buggy_action.id)
    LEFT JOIN buggy_setproject ON (buggy_setproject.action_id = buggy_action.id)
    LEFT JOIN buggy_setassignment ON (buggy_setassignment.action_id = buggy_action.id)
    LEFT JOIN buggy_setstate ON (buggy_setstate.action_id = buggy_action.id)
    LEFT JOIN buggy_setpriority ON (buggy_setpriority.action_id = buggy_action.id)
    ORDER BY bug_id, "order";


    WITH derived_bugs AS (
      SELECT buggy_bug.id,
        (SELECT min(created_at)
         FROM buggy_action
         WHERE buggy_action.bug_id = buggy_bug.id) AS "created_at",
        (SELECT max(created_at)
          FROM buggy_action
          WHERE buggy_action.bug_id = buggy_bug.id) AS "modified_at",
        (SELECT title
         FROM buggy_settitle,
              buggy_action
         WHERE buggy_settitle.action_id = buggy_action.id
           AND buggy_action.bug_id = buggy_bug.id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT state
         FROM buggy_setstate,
              buggy_action
         WHERE buggy_setstate.action_id = buggy_action.id
           AND buggy_action.bug_id = buggy_bug.id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT priority
         FROM buggy_setpriority,
              buggy_action
         WHERE buggy_setpriority.action_id = buggy_action.id
           AND buggy_action.bug_id = buggy_bug.id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT assigned_to_id
         FROM buggy_setassignment,
              buggy_action
         WHERE buggy_setassignment.action_id = buggy_action.id
           AND buggy_action.bug_id = buggy_bug.id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT user_id
         FROM buggy_action
         WHERE buggy_action.bug_id = buggy_bug.id
         ORDER BY "order" ASC LIMIT 1) AS "created_by_id",
        (SELECT project_id
         FROM buggy_setproject,
              buggy_action
         WHERE buggy_setproject.action_id = buggy_action.id
           AND buggy_action.bug_id = buggy_bug.id
         ORDER BY "order" DESC LIMIT 1)
      FROM buggy_bug
    )
    SELECT * FROM derived_bugs
    EXCEPT
    SELECT * FROM buggy_bug;


    WITH derived_bugs AS (
      SELECT ids.bug_id AS "id",
        (SELECT min(created_at)
         FROM buggy_action
         WHERE buggy_action.bug_id = ids.bug_id) AS "created_at",
        (SELECT max(created_at)
          FROM buggy_action
          WHERE buggy_action.bug_id = ids.bug_id) AS "modified_at",
        (SELECT title
         FROM buggy_settitle,
              buggy_action
         WHERE buggy_settitle.action_id = buggy_action.id
           AND buggy_action.bug_id = ids.bug_id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT state
         FROM buggy_setstate,
              buggy_action
         WHERE buggy_setstate.action_id = buggy_action.id
           AND buggy_action.bug_id = ids.bug_id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT priority
         FROM buggy_setpriority,
              buggy_action
         WHERE buggy_setpriority.action_id = buggy_action.id
           AND buggy_action.bug_id = ids.bug_id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT assigned_to_id
         FROM buggy_setassignment,
              buggy_action
         WHERE buggy_setassignment.action_id = buggy_action.id
           AND buggy_action.bug_id = ids.bug_id
         ORDER BY "order" DESC LIMIT 1),
        (SELECT user_id
         FROM buggy_action
         WHERE buggy_action.bug_id = ids.bug_id
         ORDER BY "order" ASC LIMIT 1) AS "created_by_id",
        (SELECT project_id
         FROM buggy_setproject,
              buggy_action
         WHERE buggy_setproject.action_id = buggy_action.id
           AND buggy_action.bug_id = ids.bug_id
         ORDER BY "order" DESC LIMIT 1),
        string_agg(comment, ' ') || ' ' || string_agg(title, ' ')
      FROM (SELECT DISTINCT bug_id FROM buggy_action) ids
      LEFT JOIN buggy_action ON (ids.bug_id = buggy_action.bug_id)
      LEFT JOIN buggy_settitle ON (buggy_action.id = buggy_settitle.action_id)
      LEFT JOIN buggy_comment ON (buggy_action.id = buggy_comment.action_id)
      GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
    )
    INSERT INTO buggy_bug (SELECT * FROM derived_bugs);
