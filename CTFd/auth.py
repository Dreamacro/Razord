from flask import render_template, request, redirect, abort, jsonify, url_for, session, Blueprint
from CTFd.utils import sha512, is_safe_url, authed, mailserver, sendmail, can_register
from CTFd.models import db, Teams

from itsdangerous import TimedSerializer, BadTimeSignature
from passlib.hash import bcrypt_sha256
from flask import current_app as app

import logging
import time
import re
import os

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        errors = []
        name = request.form['name']
        team = Teams.query.filter_by(name=name).first()
        if team and bcrypt_sha256.verify(request.form['password'], team.password):
            try:
                session.regenerate() # NO SESSION FIXATION FOR YOU
            except:
                pass # TODO: Some session objects don't implement regenerate :(
            session['username'] = team.name
            session['id'] = team.id
            session['admin'] = team.admin
            session['nonce'] = sha512(os.urandom(10))
            db.session.close()

            logger = logging.getLogger('logins')
            logger.warn("[{0}] {1} logged in".format(time.strftime("%m/%d/%Y %X"), session['username'].encode('utf-8')))

            # if request.args.get('next') and is_safe_url(request.args.get('next')):
            #     return redirect(request.args.get('next'))
            return redirect('/team/{0}'.format(team.id))
        else:
            errors.append("That account doesn't seem to exist")
            db.session.close()
            return render_template('login.html', errors=errors)
    else:
        db.session.close()
        return render_template('login.html')


@auth.route('/logout')
def logout():
    if authed():
        session.clear()
    return redirect('/')
