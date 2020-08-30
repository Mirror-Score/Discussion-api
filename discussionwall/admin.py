from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Post)
admin.site.register(Answer)
admin.site.register(PostReport)
admin.site.register(AnswerReport)
admin.site.register(AnswerUpvote)
admin.site.register(PostUpvote)
admin.site.register(LoginMethod)
admin.site.register(StudentBoard)
admin.site.register(StudentClass)
admin.site.register(Subject)
admin.site.register(Student)