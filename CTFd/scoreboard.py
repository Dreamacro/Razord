from flask import current_app as app, session, render_template, jsonify, Blueprint
from CTFd.utils import unix_time
from CTFd.models import db, Teams, Solves, Challenges, Checks
from CTFd.config import CHECK_SCORE, ATTACK_SCORE

scoreboard = Blueprint('scoreboard', __name__)


# # 显示
# @scoreboard.route('/scoreboard')
# def scoreboard_view():
    # score = db.func.sum(Challenges.value).label('score')
    # quickest = db.func.max(Solves.date).label('quickest')
    # teams = db.session.query(Solves.teamid, Teams.name, score).join(Teams).join(Challenges).filter(Teams.banned == None).group_by(Solves.teamid).order_by(score.desc(), quickest)
    # db.session.close()
    # return render_template('scoreboard.html', teams=teams)


# # json队伍排名积分
# @scoreboard.route('/scores')
# def scores():
    # score = db.func.sum(Challenges.value).label('score')
    # quickest = db.func.max(Solves.date).label('quickest')
    # teams = db.session.query(Solves.teamid, Teams.name, score).join(Teams).join(Challenges).filter(Teams.banned == None).group_by(Solves.teamid).order_by(score.desc(), quickest)
    # db.session.close()
    # json = {'standings':[]}
    # for i, x in enumerate(teams):
        # json['standings'].append({'pos':i+1, 'id':x.teamid, 'name':x.name,'score':int(x.score)})
    # return jsonify(json)


@scoreboard.route('/round/<round>')
def round_scoreboard(round):
    teams = Teams.query.filter_by(admin=False).all()
    chals = Challenges.query.filter_by(hidden=False).all()
    team_map = {t.id:t.name for t in teams}
    check_status = {}
    attack_status = {}
    team_score = {}
    attacked_cnt = {}

    # init
    for t in teams:
        for c in chals:
            # (team, chal)
            check_status[(t.id, c.id)] = True
            attacked_cnt[(t.id, c.id)] = 0
            for vict in teams:
                # (attack_team, victim_team, chal)
                attack_status[(t.id, vict.id, c.id)] = False
        team_score[t.id] = 0

    # check status
    checks = Checks.query.filter_by(round=round)
    for check in checks:
        if check.status != 0:
            #check down
            check_status[(check.teamid, check.chalid)] = False

    # check score
    for chal in chals:
        down_cnt = sum([1 for ((tid, cid), s) in check_status.items() if s == False and cid == chal.id])
        print down_cnt
        up_cnt = len(teams) - down_cnt
        if down_cnt == 0:
            # all up
            continue
        up_score = CHECK_SCORE * down_cnt / float(up_cnt)
        down_score = CHECK_SCORE
        for tid in team_score:
            if check_status[(tid, chal.id)]:
                # check up
                team_score[tid] += up_score
            else:
                # check down
                team_score[tid] -= down_score

    # attack status
    solves = Solves.query.filter_by(round=round)
    for solve in solves:
        vic_tid = solve.key.gamebox.teamid
        attack_status[(solve.teamid, vic_tid, solve.chalid)] = True
        attacked_cnt[(vic_tid, solve.chalid)] += 1

    # attack score
    # loss
    for (tid, cid) in attacked_cnt:
        if attacked_cnt[(tid, cid)] > 0:
            team_score[tid] -= ATTACK_SCORE
    # gain
    for (tid, vic_tid, cid) in attack_status:
        if attack_status[(tid, vic_tid, cid)]:
            team_score[tid] += ATTACK_SCORE / float(attacked_cnt[(vic_tid, cid)])

    # ouput
    ret = {}
    for (k, v) in team_score.items():
        ret[team_map[k]] = v

    db.session.close()
    return jsonify(ret)
