from django.urls import path,include
from .views import (
    PostView,PostUpvoteView,PostReportView,LoginView,
    AnswerView,AnswerReportView,AnswerUpvoteView,AnswerDetailView
)

urlpatterns = [
    path('login',LoginView.as_view(), name='login'),
    path('discussionWall/post', PostView.as_view(), name='post'),
    path('discussionWall/postupvote', PostUpvoteView.as_view(), name='post_upvote'),
    path('discussionWall/postreport', PostReportView.as_view(), name='post_report'),
    path('discussionWall/answer', AnswerView.as_view(), name='answer'),
    path('discussionWall/answerupvote', AnswerUpvoteView.as_view(), name='answer_upvote'),
    path('discussionWall/answerreport', AnswerReportView.as_view(), name='answer_report'),
    path('discussionWall/answerdetail', AnswerDetailView.as_view(), name='answer_detail'),
]