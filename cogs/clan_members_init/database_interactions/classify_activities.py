# this needs a python wrapper
# run post activities update

# this is a SQL query that classifies activities based on their text

UPDATE activities
SET activity_type = CASE
    -- Exact matches for citadel activities
    WHEN LOWER(text) = 'visited my clan citadel.' THEN 'clan - citadel visit'
    WHEN LOWER(text) = 'capped at my clan citadel.' THEN 'clan - citadel cap'
    
    -- More specific patterns should come before general ones
    WHEN text ILIKE '%I found%' AND text ILIKE '%pet%' THEN 'pet drop'
    WHEN text ILIKE '%I killed%' THEN 'combat'
	WHEN text ILIKE '%I defeated%' THEN 'combat'
    WHEN text ILIKE '%I found%' THEN 'item drop'
    WHEN text ILIKE '%XP in%' THEN 'xp milestone'
    WHEN text ILIKE '%levelled up%' THEN 'level'
    WHEN text ILIKE '%I levelled%' THEN 'level'
    WHEN text ILIKE '%total levels%' THEN 'total levels'
	WHEN text ILIKE '%levelled all skills%' THEN 'total levels'
    WHEN text ILIKE '%Quest complete%' THEN 'quest'
    WHEN text ILIKE '%treasure trail%' THEN 'clue'
	WHEN details ILIKE '%treasure hunter%' THEN 'mtx'
    WHEN text ILIKE '%clan fealty%' THEN 'clan - fealty'
	WHEN text ILIKE '%dungeon floor%' THEN 'dungeoneering'
	WHEN text ILIKE '%archaeological mystery%' THEN 'archaeology'
	WHEN text ILIKE '%quest points obtained%' THEN 'quest milestone'
	WHEN text ILIKE '%tetracompass%' THEN 'archaeology'
	WHEN text ILIKE '%songs unlocked%' THEN 'songs'
	WHEN text ILIKE '%Daemonheim''s history uncovered%' then 'dungeoneering'
	WHEN text ILIKE '%Challenged by the Skeleton Champion%' then 'distraction and diversion'
    
    -- Default classification (optional)
    ELSE NULL
END
WHERE activity_type IS NULL;