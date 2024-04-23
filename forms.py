from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, NumberRange

class RatingCommentForm(FlaskForm):
    rating = IntegerField('Оценка', validators=[InputRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Комментарий', validators=[InputRequired()])
    submit = SubmitField('Отправить')