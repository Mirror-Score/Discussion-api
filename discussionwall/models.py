from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

import os
import secrets
from datetime import datetime

MyUser = get_user_model()

class LoginMethod(models.Model):
    login_method = models.CharField(max_length=225)

# def user_profile_directory_path(instance, filename):
#     # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
#     _,ext = os.path.splitext(filename)
#     hash_name = secrets.token_hex(8)
#     filename = hash_name + ext
#     return 'user_profiles/{0}_{1}'.format(instance.user.id, filename)

# class Profile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE)
#     image = models.ImageField(default="default.svg",
#         upload_to=user_profile_directory_path)

#     def __str__(self):
#         return f"user:{self.user}"

def user_directory_path(instance, filename):
    # https://stackoverflow.com/questions/6557553/get-month-name-from-number
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    now = datetime.now()
    data = {
        'year': now.year,
        'month': now.strftime('%B'),
        'file': filename
    }
    return 'discussionwall/{year}/{month}/{file}'.format(**data)

class StudentClass(models.Model):
    studentclass = models.CharField(max_length=225)

    def __str__(self):
        return f"{self.studentclass}"

class StudentBoard(models.Model):
    studentboard = models.CharField(max_length=225)

    def __str__(self):
        return f"{self.studentboard}"

class Subject(models.Model):
    subject = models.CharField(max_length=225)

    def __str__(self):
        return f"{self.subject}"

class Student(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)
    studentclass = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    studentboard = models.ForeignKey(StudentBoard, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.get_full_name}"

class Post(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    text = models.TextField(null=True)
    image = models.ImageField(upload_to=user_directory_path,null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    studentclass = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    studentboard = models.ForeignKey(StudentBoard, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

class Answer(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)
    text = models.TextField(null=True)
    image = models.ImageField(upload_to=user_directory_path,null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

class PostReport(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    missing_option = models.BooleanField(default=False)
    missing_image = models.BooleanField(default=False)
    spelling_mistake = models.BooleanField(default=False)
    incorrect_answer = models.BooleanField(default=False)
    incorrect_question = models.BooleanField(default=False)

class AnswerReport(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    missing_option = models.BooleanField(default=False)
    missing_image = models.BooleanField(default=False)
    spelling_mistake = models.BooleanField(default=False)
    incorrect_answer = models.BooleanField(default=False)
    incorrect_question = models.BooleanField(default=False)

class PostUpvote(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

class AnswerUpvote(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
