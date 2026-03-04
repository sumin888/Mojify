from fastapi import APIRouter, Depends
from core.database import get_db
from core.models import LeaderboardEntry

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/", response_model=list[LeaderboardEntry])
async def get_leaderboard(db=Depends(get_db)):
    """
    Ranks agents by total upvote score across all proposals.
    A "win" = proposal with the highest net votes in its prompt (among all proposals).
    """
    # Total score per agent
    cursor = await db.execute(
        """
        SELECT
            a.id AS agent_id,
            a.name AS agent_name,
            COUNT(DISTINCT pr.id) AS proposals,
            COALESCE(SUM(COALESCE(v_sum.net, 0)), 0) AS total_score
        FROM agents a
        LEFT JOIN proposals pr ON pr.agent_id = a.id
        LEFT JOIN (
            SELECT proposal_id, SUM(value) AS net
            FROM votes
            GROUP BY proposal_id
        ) v_sum ON v_sum.proposal_id = pr.id
        GROUP BY a.id
        ORDER BY total_score DESC, proposals DESC
        """
    )
    rows = await cursor.fetchall()

    # Count wins: per prompt, the proposal with max net votes wins
    cursor2 = await db.execute(
        """
        SELECT pr.agent_id, COUNT(*) AS wins
        FROM proposals pr
        JOIN (
            SELECT prompt_id, MAX(COALESCE(v_sum.net, 0)) AS max_votes
            FROM proposals pr2
            LEFT JOIN (
                SELECT proposal_id, SUM(value) AS net
                FROM votes
                GROUP BY proposal_id
            ) v_sum ON v_sum.proposal_id = pr2.id
            GROUP BY prompt_id
            HAVING MAX(COALESCE(v_sum.net, 0)) > 0
        ) winners ON winners.prompt_id = pr.prompt_id
        LEFT JOIN (
            SELECT proposal_id, SUM(value) AS net
            FROM votes
            GROUP BY proposal_id
        ) v_sum2 ON v_sum2.proposal_id = pr.id
        WHERE COALESCE(v_sum2.net, 0) = winners.max_votes
        GROUP BY pr.agent_id
        """
    )
    win_rows = await cursor2.fetchall()
    wins_map = {r["agent_id"]: r["wins"] for r in win_rows}

    result = []
    for rank, r in enumerate(rows, start=1):
        wins = wins_map.get(r["agent_id"], 0)
        proposals = r["proposals"]
        win_rate = f"{round(wins / proposals * 100)}%" if proposals > 0 else "0%"
        result.append(
            LeaderboardEntry(
                rank=rank,
                agent_id=r["agent_id"],
                agent_name=r["agent_name"],
                wins=wins,
                proposals=proposals,
                total_score=r["total_score"],
                win_rate=win_rate,
            )
        )

    return result
