from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[
        DataRequired(),
        Length(min=3, max=80, message='用户名长度在3-80个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=6, message='密码至少6个字符')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('用户名已被使用')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('邮箱已被注册')


class UploadForm(FlaskForm):
    image = FileField('选择图片', validators=[
        FileRequired(message='请选择图片文件'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], '仅支持图片格式')
    ])
    title = StringField('标题', validators=[Length(max=200)])
    description = TextAreaField('描述')
    tags = StringField('标签（用逗号分隔）')
    is_public = BooleanField('公开图片', default=True)
    submit = SubmitField('上传')