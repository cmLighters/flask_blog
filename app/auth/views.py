# -*- coding: utf-8 -*-

from . import auth
from .. import db
from flask import render_template, request, url_for, redirect, flash, current_app
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    ResetPasswordRequestForm, ResetPasswordForm, ChangeEmailForm
from ..models import User
from ..email import send_email
from flask_login import login_user, logout_user, login_required, current_user
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    #feedback = ''
    if form.validate_on_submit():
        #email = form.email.data
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('用户名或密码错误')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已退出账户')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        send_email(form.email.data, 'Confirm Your Account',
                   'auth/mail/confirm', user=user, token=user.generate_confirmation_token())
        flash('确认邮件已发送到您的注册邮箱中')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.before_app_request
def please_confirm():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')


@auth.route('/reconfirm')
@login_required
def resend_confirmation():
    if current_user.confirmed:
        flash('您的账户已确认')
        redirect(url_for('main.index'))
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'cmLighters\' Blog 注册邮箱确认',
               'auth/mail/confirm', user=current_user, token=token)
    flash('新的账户验证邮件已发送到您的邮箱中')
    return redirect(url_for('auth.login'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()     # commit user confirmed status change to db
        flash('账户验证成功，感谢您的使用')
    else:
        flash('无效的账户验证链接或链接已过期')
    return redirect(url_for('main.index'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('密码错误')
        else:
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('密码更新成功')
            return redirect(url_for('main.index'))
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if not u is None:
            token = u.generate_reset_password_token()
            send_email(u.email, 'Reset %s password'%u.username, 'auth/mail/reset_password',
                       user=u, token=token, next=request.args.get('next'))
            flash('重置密码邮件已发送到您的邮箱中')
            return redirect(url_for('auth.login'))
        else:
            flash('邮箱未被注册')
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.new_password.data):
            return redirect(url_for('auth.login'))
        else:
            flash('重置密码链接无效或已过期')
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_change_email_token(new_email)
            send_email(new_email, 'cmLighters\' Blog 用户邮箱更改',
                       'auth/mail/change_email', token=token, user=current_user)
            flash('确认链接邮件已发送到您的新邮箱中')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('您的邮箱地址更新成功')
    else:
        flash('更新邮箱链接无效或已过期')
    return redirect(url_for('main.index'))

