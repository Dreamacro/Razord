#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from flask import current_app as app, render_template, request, redirect, abort, jsonify, json as json_mod, url_for, session, Blueprint

from CTFd.utils import ctftime, view_after_ctf, authed, unix_time, get_kpm, can_view_challenges, is_admin, get_config
from CTFd.models import db, Challenges, Files, Solves, WrongKeys, Keys, Gameboxs, Rounds

import time
import re
import logging
import json

challenges = Blueprint('challenges', __name__)


@challenges.route('/challenges', methods=['GET'])
def challenges_view():
    if not is_admin():
        if not ctftime():
            if view_after_ctf():
                pass
            else:
                return redirect('/')
    if can_view_challenges():
        return render_template('chals.html', ctftime=ctftime())
    else:
        return redirect('/login')


# 前端获取题目信息
@challenges.route('/chals', methods=['GET'])
def chals():
    if not is_admin():
        if not ctftime():
            if view_after_ctf():
                pass
            else:
                return redirect('/')
    if can_view_challenges():
        chals = Challenges.query.add_columns('id', 'name', 'value', 'description', 'category').order_by(Challenges.value).all()

        json = {'game':[]}
        for x in chals:
            files = [ str(f.location) for f in Files.query.filter_by(chal=x.id).all() ]
            json['game'].append({'id':x[1], 'name':x[2], 'value':x[3], 'description':x[4], 'category':x[5], 'files':files})

        db.session.close()
        return jsonify(json)
    else:
        db.session.close()
        return redirect('/login')


@challenges.route('/chals/solves')
def chals_per_solves():
    if can_view_challenges():
        solves = Solves.query.add_columns(db.func.count(Solves.chalid)).group_by(Solves.chalid).all()
        json = {}
        for chal, count in solves:
            json[chal.chal.name] = count
        return jsonify(json)
    return redirect('/login')


# 前端获取队伍解题情况
@challenges.route('/solves')
@challenges.route('/solves/<teamid>')
def solves(teamid=None):
    if teamid is None:
        if authed():
            solves = Solves.query.filter_by(teamid=session['id']).all()
        else:
            abort(401)
    else:
        solves = Solves.query.filter_by(teamid=teamid).all()
    db.session.close()
    json = {'solves':[]}
    for x in solves:
        json['solves'].append({ 'chal':x.chal.name, 'chalid':x.chalid,'team':x.teamid, 'value': x.chal.value, 'category':x.chal.category, 'time':unix_time(x.date)})
    return jsonify(json)


# 前端获取
@challenges.route('/maxattempts')
def attempts():
    chals = Challenges.query.add_columns('id').all()
    json = {'maxattempts':[]}
    for chal, chalid in chals:
        fails = WrongKeys.query.filter_by(team=session['id'], chalid=chalid).count()
        if fails >= int(get_config("max_tries")) and int(get_config("max_tries")) > 0:
            json['maxattempts'].append({'chalid':chalid})
    return jsonify(json)


# 前端获取答题成功失败情况
@challenges.route('/fails/<teamid>', methods=['GET'])
def fails(teamid):
    fails = WrongKeys.query.filter_by(team=teamid).count()
    solves = Solves.query.filter_by(teamid=teamid).count()
    db.session.close()
    json = {'fails':str(fails), 'solves': str(solves)}
    return jsonify(json)


# 用来显示提交该题FLAG的队伍
@challenges.route('/chal/<chalid>/solves', methods=['GET'])
def who_solved(chalid):
    solves = Solves.query.filter_by(chalid=chalid).order_by(Solves.date.asc())
    json = {'teams':[]}
    for solve in solves:
        json['teams'].append({'id':solve.team.id, 'name':solve.team.name, 'date':solve.date})
    return jsonify(json)


# init testdb
@challenges.route('/testinit', methods=['GET'])
def ttestinit():
    chal = Challenges('chal1', 'desc', 100, 'RE', 'noflag')
    gamebox = Gameboxs(1, 1, '192.168.1.10')
    round = Rounds()
    key = Keys(1, 'nooflag', 0, 1, 1)
    db.session.add(chal)
    db.session.add(gamebox)
    db.session.add(key)
    db.session.add(round)
    db.session.commit()

    return '1'


# 统一了flag的提交接口
@challenges.route('/submit_flag', methods=['POST'])
def submit_flag():
    result = {}
    if not ctftime():
        return redirect('/challenges')
    if authed():
        submitkey = str(request.form['key'].strip().lower())
        teamid = session['id']
        request_ip = request.remote_addr
        querykey = Keys.query.filter_by(flag=submitkey).first()
        if querykey:
            # Right key
            querysolve = Solves.query.filter_by(keyid=querykey.id, teamid=teamid).first()
            if querysolve:
                # Already submitted
                result['status'] = 2
                result['msg'] = 'Already submitted'
            else:
                newsolve = Solves(querykey.id, teamid, request_ip)
                db.session.add(newsolve)
                db.session.commit()
                result['status'] = 1
                result['msg'] = 'Right Flag'
        else:
            result['status'] = 0
            result['msg'] = 'Wrong Flag'
    else:
        result['status'] = -1
        result['msg'] = 'Login First'
    return json.dumps(result)
    # solves = Solves.query.join(Keys).filter(Solves.teamid==session['id']).first()


# 弃用此接口改用统一的提交接口
@challenges.route('/chal/<chalid>', methods=['POST'])
def chal(chalid):
    if not ctftime():
        return redirect('/challenges')
    if authed():
        solves = Solves.query.join(Keys).filter(Solves.teamid==session['id'], ).first()
        # Challange not solved yet
        if not solves:
            chal = Challenges.query.filter_by(id=chalid).first()
            key = str(request.form['key'].strip().lower())
            keys = json.loads(chal.flags)
            findkey = None#TODO Query
            if findkey:
                chalid = findkey.chal.id
                solve = Solves(keyid=findkey.id, teamid=session['id'], ip=request.remote_addr)
                db.session.add(solve)
                db.session.commit()
                db.session.close()
                return "1" # key was correct
            return '0' # key was wrong

        # Challenge already solved
        else:
            logger.info("{0} submitted {1} with kpm {2} [ALREADY SOLVED]".format(*data))
            return "2" # challenge was already solved
    else:
        return "-1"
