from os import path
from uuid import uuid4

from flask import flash, url_for, redirect, render_template, Blueprint, request
from jmilkfansblog.forms import LoginForm, RegisterForm, OpenIDForm

from jmilkfansblog.models import db, User
from jmilkfansblog.extensions import openid, facebook, twitter


# Create the blueprint object
main_blueprint = Blueprint(
    'main',
    __name__,
    template_folder=path.join(path.pardir, 'templates', 'main'))


@main_blueprint.route('/')
def index():
    """Will be default callable when request url is `/`."""
    return redirect(url_for('blog.home'))


@main_blueprint.route('/login', methods=['GET', 'POST'])
@openid.loginhandler
def login():
    """View function for login.
       
       Flask-OpenID will be receive the Authentication-information
       from relay party.
    """

    # Create the object for LoginForm
    form = LoginForm()
    # Create the object for OpenIDForm
    openid_form = OpenIDForm()

    # Send the request for login to relay party(URL).
    if openid_form.validate_on_submit():
        return openid.trg_login(
            openid_form.openid_url.data,
            ask_for=['nickname', 'email'],
            ask_for_optional=['fullname'])

    # Try to login the relay party failed.
    openid_errors = openid.fetch_error()
    if openid_errors:
        flash(openid_errors, category="danger")

    # Will be check the account whether rigjt.
    if form.validate_on_submit():
        flash("You have been logged in.", category="success")
        return redirect(url_for('blog.home'))

    return render_template('login.html',
                           form=form,
                           openid_form=openid_form)


@main_blueprint.route('/logout', methods=['GET', 'POST'])
def logout():
    """View function for logout."""

    flash("You have been logged out.", category="success")
    return redirect(url_for('blog.home'))


@main_blueprint.route('/register', methods=['GET', 'POST'])
@openid.loginhandler
def register():
    """View function for Register."""

    # Create the form object for RegisterForm.
    form = RegisterForm()
    # Create the form object for OpenIDForm.
    openid_form = OpenIDForm()

    # Send the request for login to relay party(URL).
    if openid_form.validate_on_submit():
        return openid.try_login(
            openid_from.openid_url.data,
            ask_for=['nickname', 'email'],
            ask_for_optional=['fullname'])

    # Try to login the relay party failed.
    openid_errors = openid.fetch_error()
    if openid_errors:
        flash(openid_errors, category='danger')

    # Will be check the username whether exist.
    if form.validate_on_submit():
        new_user = User(id=str(uuid4()),
                        username=form.username.data,
                        password=form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash('Your user has been created, please login.',
              category="success")

        return redirect(url_for('main.login'))
    return render_template('register.html',
                           form=form,
                           openid_form=openid_form)


@main_blueprint.route('/facebook')
def facebook_login():
    return facebook.authorize(
        callback=url_for('main.facebook_authorized',
                         next=request.referrer or None,
                         _external=True))


@main_blueprint.route('/facebook/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description'])

    session['facebook_oauth_token'] = (resp['access_token'], '')

    me = facebook.get('/me')
    user = User.query.filter_by(
        username=me.data['filter_name'] + " " + me.data['last_name']).first()
    if not user:
        user = User(id=str(uuid4()), username=me.data['filter_name'] + " " + me.data['last_name'], password='jmilkfan')
        db.session.add(user)
        db.session.commit()

    flash('You have been logged in.', category='success')

    return redirect(
        request.args.get('next') or url_for('blog.home'))


@main_blueprint.route('/twitter-login')
def twitter_login():
    return twitter.authorize(
        callback=url_for(
            'main.twitter_authorized',
            next=request.referrer or None,
            _external=True))


@main_blueprint.route('/twitter-login/authorized')
@twitter.authorized_handler
def twitter_authorized(resp):
    if resp is None:
        return 'Access denied: reason: {} error:{}'.format(
            request.args['error_reason'],
            request.args['error_description'])

    session['twitter_oauth_token'] = resp['oauth_token'] + \
        resp['oauth_token_secret']

    user = User.query.filter_by(
        username=resp['screen_name']).first()

    if not user:
        user = User(id=str(uuid4()), username = resp['screen_name'], password='jmilkfan')
        db.session.add(user)
        db.session.commit()


    flash("You have been logged in.", category="success")
    return redirect(
        request.args.get('next') or url_for('blog.home'))
