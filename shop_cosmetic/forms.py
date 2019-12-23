from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from shop_cosmetic.models import User
from flask_admin import AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import ActionsMixin
from flask_admin.form import rules
from flask_ckeditor import CKEditorField
from shop_cosmetic import bcrypt
from flask import flash, redirect, url_for, request


class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=2,max=20)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')]) 
	submit = SubmitField('Sign up')
	
	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('That username is taken. Please choose a different one. ')
	def validate_email(self, email):
		if User.query.filter_by(email=email.data).first():
			raise ValidationError('Email already registered.')


class LoginForm(FlaskForm): 
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')	


class UpdateAccountForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	old_pass = PasswordField('Old password')
	new_pass = PasswordField('New password')
	confirm_pass = PasswordField('Confirm password', validators=[EqualTo('new_pass')])
	submit = SubmitField('Update')

	def validate_username(self, username):
		if username.data != current_user.username:
			user = User.query.filter_by(username=username.data).first()
			if user:
				raise ValidationError('That username is taken. Please choose a different one')

	def validate_email(self, email):
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('That email is taken. Please choose a different one')


class ProductForm(FlaskForm):
	p_name = StringField('Title', validators=[DataRequired()])
	description = CKEditorField('Description', validators=[DataRequired()])
	price = FloatField('Price', validators=[DataRequired()])
	picture = FileField('Product image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
	submit = SubmitField('Add')


class UserAdminView(ModelView, ActionsMixin):
	column_searchable_list = ('username',)
	column_sortable_list = ('username', 'admin')
	column_exclude_list = ('password',)
	form_excluded_columns = ('password',)
	form_edit_rules = ('username', 'admin',  rules.Header('Reset Password'), 'new_password', 'confirm')
	form_create_rules = ('username', 'admin', 'email', 'password')

	def is_accessible(self):
		return current_user.is_authenticated and current_user.is_admin()

	def inaccessible_callback(self, name, **kwargs):
		return redirect(url_for('home', next=request.url))

	def scaffold_form(self):
		form_class = super(UserAdminView, self).scaffold_form()
		form_class.password = PasswordField('Password')
		form_class.new_password = PasswordField('New Password')
		form_class.confirm = PasswordField('Confirm New Password')
		return form_class

	def create_model(self, form):
		model = self.model(
			form.username.data, form.password.data, form.admin.data
		)
		form.populate_obj(model)
		model.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		self.session.add(model)
		self._on_model_change(form, model, True)
		self.session.commit()

	def update_model(self, form, model):
		form.populate_obj(model)
		if form.new_password.data:
			if form.new_password.data != form.confirm.data:
				flash('Passwords must match')
				return
			model.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
		self.session.add(model)
		self._on_model_change(form, model, False)
		self.session.commit()


class AdminView(AdminIndexView):
	def is_accessible(self):
		return current_user.is_authenticated and current_user.is_admin()

	def inaccessible_callback(self, name, **kwargs):
		return redirect(url_for('home', next=request.url))

class HomeView(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('home'))