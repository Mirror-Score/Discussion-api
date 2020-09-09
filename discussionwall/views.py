from rest_framework import serializers,status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken


from django.conf import settings
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.contrib.auth import get_user_model

SUCCESS = settings.SUCCESS
FAIL = settings.FAIL

# from user.models import MyUser
# from doubt.models import Subject
from .decorators import authorization_required
from .models import Post, Answer, PostUpvote, AnswerUpvote, PostReport, AnswerReport,Subject

MyUser = get_user_model()

class LoginView(TokenObtainPairView):
    """
    Required fiels:
        - email
        - password
    """
    def post(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        if not email:
            raise serializers.ValidationError('Email is required')
        if not password:
            raise serializers.ValidationError('password is required')
        user = MyUser.objects.filter(email__iexact=email).first()
        if user and user.check_password(password):
            tokens = self.get_tokens_for_user(user)
            SUCCESS['Result'] = {
                'userId': user.id,
                'token': tokens
            }
            return Response(SUCCESS, status=200)
        FAIL['Comments'] = "Invalid email or password"
        return Response(FAIL, status=404)

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        

class Paginate:
    
    count = 0
    next = None
    previous = None
    page_query = None
    page_size = settings.DEFAULT_PAGE_SIZE

    def paginate(self, request, query, page_size=None, *args, **kwargs):
        if page_size:
            self.page_size = page_size
        current_page = request.query_params.get('page') or 1
        page_object = Paginator(query, self.page_size)
        self.count = page_object.num_pages
        if int(current_page) <= self.count:
            self.page_query = page_object.page(current_page)
            # if self.page_query.has_next():
            #     self.next = self.page_query.next_page_num()
            # if self.page_query.has_previous():
            #     self.previous = self.page_query.previous_page_num()
        data = {
            'count': self.count,
            # 'next': self.next,
            # 'previous': self.previous,
            'data': []
        }
        return [self.page_query,data]



class PostView(APIView,Paginate):
    authentication_class = [JWTAuthentication]
    permission_class = [IsAuthenticated]
    
    @method_decorator(authorization_required)
    def get(self, request, *args, **kwargs):
        user = request.user
        posts = Post.objects.all().order_by('-created_on')
        posts,data = self.paginate(request, posts)
        if posts:
            for post in posts:
                upvote = PostUpvote.objects.filter(user=user, post=post).exists()
                report = PostReport.objects.filter(user=user, post=post).exists()
                answer_count = post.answer_set.filter(parent__isnull=True).count()
                upvote_count = post.postupvote_set.all().count()
                report_count = post.postreport_set.all().count()
                p = {
                    'postId': post.id,
                    'userId': post.user.id,
                    # 'role': post.user.role.role,
                    'userName': post.user.get_full_name(),
                    # 'userImage': post.user.profile.image.url,
                    'text': post.text,
                    'image': '',
                    'createdOn': naturaltime(post.created_on),
                    'updatedOn': naturaltime(post.updated_on),
                    'studentClass': post.studentclass.studentclass,
                    'studentBoard': post.studentboard.studentboard,
                    'subject': post.subject.subject,
                    'answerCount': answer_count,
                    'upvoteCount': upvote_count,
                    'upvoted': upvote,
                    'reportCount': report_count,
                    'reported': report
                }
                if post.image:
                    p['image'] = post.image.url
                if report:
                    report = PostReport.objects.filter(user=user, post=post).first()
                    p['report'] = {
                        'reportId': report.id,
                        'missingOption': report.missing_option,
                        'missingImage': report.missing_image,
                        'spellingMistake': report.spelling_mistake,
                        'incorrectAnswer': report.incorrect_answer,
                        'incorrectQuestion': report.incorrect_answer
                    }
                data['data'].append(p)
            print(data)
            SUCCESS['Result'] = data
            SUCCESS['Comments'] = "Posts fetched successfully"
            return Response(SUCCESS, status=status.HTTP_200_OK)
        FAIL['Comments'] = "Page does not exists"
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)


    @method_decorator(authorization_required)
    def post(self, request, *args, **kwagrs):
        data = request.data
        text = data.get('text')
        image = data.get('image')
        subject = data.get('subjectId')
        print(data,subject)
        if not subject:
            print('subject is required')
            raise serializers.ValidationError('subjectId is required.')
        if not (text or image):
            raise serializers.ValidationError("Either text or image is required.")

        post = Post(
            user = request.user,
            text = text,
            studentclass = request.user.student.studentclass,
            studentboard = request.user.student.studentboard,
            subject = get_object_or_404(Subject, id=subject),
        )
        if image:
            post.image = image

        post.save()
        SUCCESS['Result'] = {
            'postId': post.id,
            'userId': post.user.id,
            # 'role': post.user.role.role,
            'userName': post.user.get_full_name(),
            # 'userImage': post.user.profile.image.url,
            'text': post.text,
            'image': post.image.url if image else '',
            'createdOn': naturaltime(post.created_on),
            'updatedOn': naturaltime(post.updated_on),
            'studentClass': post.studentclass.studentclass,
            'studentBoard': post.studentboard.studentboard,
            'subject': post.subject.subject,
            'answerCount': 0,
            'upvoteCount': 0,
            'upvoted': False,
            'reportCount': 0,
            'reported': False
        }
        SUCCESS['Comments'] = 'Post created successfully'
        return Response(SUCCESS, status=status.HTTP_201_CREATED)

    @method_decorator(authorization_required)
    def put(self, request, *args, **kwagrs):
        data = request.data
        user = request.user
        text = data.get('text')
        image = data.get('image')
        post_id = data.get('postId')
        if not post_id:
            raise serializers.ValidationError("postId is required.")
        if not Post.objects.filter(id=post_id).exists():
            raise serializers.ValidationError("No post associated with postId {}".format(post_id))
        post = Post.objects.filter(id=post_id, user=request.user).first()
        if post:
            if not (text or image):
                raise serializers.ValidationError("Either text or image is required.")
            
            post = get_object_or_404(Post, id=post_id, user=request.user)
            if text:
                post.text = text
            else:
                post.text = ""
            if image:
                post.image = image
            else:
                post.image.delete()
            post.save()

            upvote = PostUpvote.objects.filter(user=user, post=post).exists()
            report = PostReport.objects.filter(user=user, post=post).exists()
            answer_count = post.answer_set.filter(parent__isnull=True).count()
            upvote_count = post.postupvote_set.all().count()
            report_count = post.postreport_set.all().count()
            SUCCESS['Comments'] = 'Post updated successfully'
            SUCCESS['Result'] = {
                'postId': post.id,
                'userId': post.user.id,
                # 'role': post.user.role.role,
                'userName': post.user.get_full_name(),
                # 'userImage': post.user.profile.image.url,
                'text': post.text,
                'image': post.image.url if image else '',
                'createdOn': naturaltime(post.created_on),
                'updatedOn': naturaltime(post.updated_on),
                'studentClass': post.studentclass.studentclass,
                'studentBoard': post.studentboard.studentboard,
                'subject': post.subject.subject,
                'answerCount': answer_count,
                'upvoteCount': upvote_count,
                'upvoted': upvote,
                'reportCount': report_count,
                'reported': report
            }
            if report:
                report = PostReport.objects.filter(user=user, post=post).first()
                SUCCESS['Result']['report'] = {
                    'reportId': report.id,
                    'missingOption': report.missing_option,
                    'missingImage': report.missing_image,
                    'spellingMistake': report.spelling_mistake,
                    'incorrectAnswer': report.incorrect_answer,
                    'incorrectQuestion': report.incorrect_answer
                }
            return Response(SUCCESS, status=status.HTTP_201_CREATED)
        FAIL['Comments'] = "Post does not exist"
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)
    
    @method_decorator(authorization_required)
    def delete(self, request, *args, **kwargs):
        data = request.data
        post_id = data.get('postId')
        if not post_id:
            raise serializers.ValidationError("postId is required")
        post = Post.objects.filter(id=post_id, user=request.user)
        if post:
            post.delete()
            SUCCESS['Result'] = 'Post deleted successfully'
            SUCCESS['Comments'] = 'Post deleted successfully'
            return Response(SUCCESS, status=status.HTTP_200_OK)
        FAIL['Comments'] = 'Post not found'
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)

class PostUpvoteView(APIView):
    authentication_class = [JWTAuthentication]
    permission_class = [IsAuthenticated]

    @method_decorator(authorization_required)
    def post(self, request, *args, **kwargs):
        data = request.data
        post_id = data.get('postId')
        if not post_id:
            raise serializers.ValidationError('postId is required.')
        post = get_object_or_404(Post, id=post_id)
        user = request.user
        upvote, created = PostUpvote.objects.get_or_create(
            user = user,
            post_id = post.id
        )
        SUCCESS['Comments'] = "post upvoted"
        if not created:
            SUCCESS['Result'] = 'Upvoted already'
            return Response(SUCCESS, status=status.HTTP_208_ALREADY_REPORTED)
        SUCCESS['Result'] = 'Upvoted post successfully.'
        return Response(SUCCESS, status=status.HTTP_201_CREATED)

class PostReportView(APIView):
    authentication_class = [JWTAuthentication]
    permission_class = [IsAuthenticated]

    @method_decorator(authorization_required)
    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        post_id = data.get('postId')
        if not post_id:
            raise serializers.ValidationError("postId is reqired")
        report_keys = {
            'missingOption':'missing_option',
            'missingImage':'missing_image',
            'spellingMistake':'spelling_mistake',
            'incorrectAnswer':'incorrect_answer',
            'incorrectQuestion':'incorrect_question'
        }
        report_val = {}
        for key in data:
            if key in report_keys:
                if data[key]!='true':
                    raise serializers.ValidationError("Invalid {} value".format(key))
                report_val.update({report_keys[key]: True})
        if not report_val:
            raise serializers.ValidationError("At least one value should be true")
        # missing_option = data.get('missingOption')
        # missing_image = data.get('missingImage')
        # spelling_mistake = data.get('spellingMistake')
        # incorrect_answer = data.get('incorrectAnswer')
        # incorrect_question = data.get('incorrectQuestion')
        # if not post_id:
        #     raise serializers.ValidationError('postId is required.')
        # if missing_option and missing_option!='true':
        #     raise serializers.ValidationError('Invalid missingOption value.')
        # if missing_image and missing_image!='true':
        #     raise serializers.ValidationError('Invalid missingImage value.')
        # if spelling_mistake and spelling_mistake!='true':
        #     raise serializers.ValidationError('Invalid spellingMistake value.')
        # if incorrect_answer and incorrect_answer!='true':
        #     raise serializers.ValidationError('Invalid invalidAnswer value.')
        # if incorrect_question and incorrect_question!='true':
        #     raise serializers.ValidationError('Invalid incorrectQuestion value.')
        post = get_object_or_404(Post, id=post_id)
        user = request.user
        report, created = PostReport.objects.update_or_create(
            post = post,user = user,
            defaults = report_val
        )
        SUCCESS['Result'] = {
            'reportId': report.id,
            'missingOption': report.missing_option,
            'missingImage': report.missing_image,
            'spellingMistake': report.spelling_mistake,
            'incorrectAnswer': report.incorrect_answer,
            'incorrectQuestion': report.incorrect_answer
        }
        if created:
            SUCCESS['Comments'] = 'Reported post successfully.'
            return Response(SUCCESS, status=status.HTTP_201_CREATED)
        SUCCESS['Comments'] = 'Update post report successfully'
        return Response(SUCCESS, status=status.HTTP_201_CREATED)

    @method_decorator(authorization_required)
    def put(self, request, *args, **kwargs):
        data = request.data
        post_id = data.get('postId')
        if not post_id:
            raise serializers.ValidationError("postId is reqired")
        report_keys = {
            'missingOption':'missing_option',
            'missingImage':'missing_image',
            'spellingMistake':'spelling_mistake',
            'incorrectAnswer':'incorrect_answer',
            'incorrectQuestion':'incorrect_question'
        }
        report_val = {
            'missing_option': False,
            'missing_image': False,
            'spelling_mistake': False,
            'incorrect_answer': False,
            'incorrect_question': False,
        }
        for key in data:
            if key in report_keys:
                if data[key]!='true':
                    raise serializers.ValidationError("Invalid {} value".format(key))
                report_val.update({report_keys[key]: True})
        if not report_val:
            raise serializers.ValidationError("At least one value should be true")

        report = PostReport.objects.filter(post_id=post_id,user=request.user)
        if report:
            report.update(**report_val)
            report = report.first()
            SUCCESS['Result'] = {
                'reportId': report.id,
                'missingOption': report.missing_option,
                'missingImage': report.missing_image,
                'spellingMistake': report.spelling_mistake,
                'incorrectAnswer': report.incorrect_answer,
                'incorrectQuestion': report.incorrect_answer
            }
            SUCCESS['Comments'] = 'Update post report successfully'
            return Response(SUCCESS, status=status.HTTP_201_CREATED)
        FAIL['Comments'] = 'Post not found'
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)

class AnswerView(APIView, Paginate):

    @method_decorator(authorization_required)
    def get(self, request, *args, **kwargs):
        """
        fetch all the answer associated with a post
            required fields:
                - postId
        """
        data = request.data
        user = request.user
        post_id = data.get('postId')
        # parent_id = data.get('parentId')
        if not post_id:
            raise serializers.ValidationError("postId is required.")
        if not Post.objects.filter(id=post_id).exists():
            raise serializers.ValidationError("No post associated with postId {}".format(post_id))
        answers = Answer.objects.filter(post_id=post_id, parent=None).order_by('-created_on')
        answers, data = self.paginate(request, answers)
        del data['data']
        post = Post.objects.get(id=post_id)
        data.update({
            'postId': post.id,
            'userId': post.user.id,
            'userName': post.user.get_full_name(),
            # 'userImage': post.user.profile.image.url,
            'text': post.text,
            'image': ''
        })
        if post.image:
            data['image'] = post.image.url
        data['data'] = []
        for ans in answers:
            upvote = AnswerUpvote.objects.filter(user=user, answer=ans).exists() # check wether user has upvoted answer
            report = AnswerReport.objects.filter(user=user, answer=ans).exists() # check wether user has reported answer
            reply_count = ans.answer_set.filter().count() # count the number of reply
            upvote_count = ans.answerupvote_set.all().count() # count the number of upvote
            report_count = ans.answerreport_set.all().count() # count the number of report
            a = {
                'answerId': ans.id,
                'userId': ans.user.id,
                # 'userRole': ans.user.role.role,
                'userName': ans.user.get_full_name(),
                # 'userImage': ans.user.profile.image.url,
                'postId': ans.post.id,
                'text': ans.text,
                'image': '',
                'createdOn': naturaltime(ans.created_on),
                'updatedOn': naturaltime(ans.updated_on),
                # 'studentClass': ans.post.studentclass.studentclass,
                # 'studentBoard': ans.post.studentboard.studentboard,
                # 'subject': ans.post.subject.subject,
                'replyCount': reply_count,
                'upvoteCount': upvote_count,
                'upvoted': upvote,
                'reportCount': report_count,
                'reported': report
            }
            if ans.image:
                a['image'] = ans.image.url
            if report:
                report = AnswerReport.objects.filter(user=user, answer=ans).first()
                a['report'] = {
                    'reportId': report.id,
                    'missingOption': report.missing_option,
                    'missingImage': report.missing_image,
                    'spellingMistake': report.spelling_mistake,
                    'incorrectAnswer': report.incorrect_answer,
                    'incorrectQuestion': report.incorrect_answer
                }
            data['data'].append(a)
        SUCCESS['Result'] = data
        return Response(SUCCESS, status=status.HTTP_200_OK)

    @method_decorator(authorization_required)
    def post(self, request, *args, **kwargs):
        data = request.data
        post_id = data.get('postId')
        parent_id = data.get('parentId')
        text = data.get('text')
        image = data.get('image')
        if not post_id:
            raise serializers.ValidationError("postId is required.")
        if not (text or image):
            raise serializers.ValidationError("Either text or image is required.")
        if parent_id and not Answer.objects.filter(id=parent_id).exists():
            raise serializers.ValidationError('No answer associated with parentId {}'.format(parent_id))
        post = get_object_or_404(Post, id=post_id)
        answer = Answer(
            user = request.user,
            post = post,
            text = text
        )
        if parent_id:
            parent = get_object_or_404(Answer, id=parent_id)
            answer.parent = parent
        if image:
            answer.image = image
        answer.save()
        SUCCESS['Result'] = "Answer saved successfully"
        return Response(SUCCESS, status=status.HTTP_201_CREATED)

    @method_decorator(authorization_required)
    def put(self, request, *args, **kwargs):
        data = request.data
        ans_id = data.get('answerId')
        text = data.get('text')
        image = data.get('image')
        if not ans_id:
            raise serializers.ValidationError("answerId is reqired")
        answer = Answer.objects.filter(id=ans_id, user=request.user).first()
        if answer:
            if not (text or image):
                raise serializers.ValidationError("Either text or image is required.")
            if image:
                answer.image = image
            else:
                answer.image.delete()
            if text:
                answer.text = text
            else:
                answer.text = ''
            answer.save()
            SUCCESS['Comments'] = "Answer updated successfully"
            SUCCESS['Result'] = {
                'answerId': ans_id,
                'text': answer.text,
                'image': answer.image.url if answer.image else '',
            }
            return Response(SUCCESS, status=status.HTTP_201_CREATED)
        FAIL['Comments'] = "Answer not found"
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)

    @method_decorator(authorization_required)
    def delete(self, request, *args, **kwargs):
        data = request.data
        answer_id = data.get('answerId')
        if not answer_id:
            raise serializers.ValidationError("answerId is required.")
        answer = Answer.objects.filter(id=answer_id,user=request.user)
        if answer:
            answer.delete()
            SUCCESS['Comments'] = "Answer deleted successfully"
            SUCCESS['Result'] = "Answer deleted successfully"
            return Response(SUCCESS, status=status.HTTP_200_OK)
        FAIL['Comment'] = "Answer not found"
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)


class AnswerUpvoteView(APIView):
    @method_decorator(authorization_required)
    def post(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        answer_id = data.get('answerId')
        if not answer_id:
            raise serializers.ValidationError('answerId is required.')
        answer = get_object_or_404(Answer, id=answer_id)
        upvote, created = AnswerUpvote.objects.get_or_create(
            user = user,
            answer_id = answer.id
        )
        SUCCESS['Comments'] = "Answer upvoted"
        if not created:
            SUCCESS['Result'] = 'Upvoted already'
            return Response(SUCCESS, status=status.HTTP_208_ALREADY_REPORTED)
        SUCCESS['Result'] = 'Upvoted answer successfully.'
        return Response(SUCCESS, status=status.HTTP_201_CREATED)

class AnswerReportView(APIView):
    @method_decorator(authorization_required)
    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        answer_id = data.get('answerId')
        if not answer_id:
            raise serializers.ValidationError("answerId is required")
        report_keys = {
            'missingOption':'missing_option',
            'missingImage':'missing_image',
            'spellingMistake':'spelling_mistake',
            'incorrectAnswer':'incorrect_answer',
            'incorrectQuestion':'incorrect_question'
        }
        report_val = {}
        for key in data:
            if key in report_keys:
                if data[key]!='true':
                    raise serializers.ValidationError("Invalid {} value".format(key))
                report_val.update({report_keys[key]: True})
        if not report_val:
            raise serializers.ValidationError("At least one value should be true")

        answer = get_object_or_404(Answer, id=answer_id)
        user = request.user
        report, created = AnswerReport.objects.update_or_create(
            answer = answer,user = user,
            defaults = report_val
        )
        SUCCESS['Result'] = {
            'reportId': report.id,
            'missingOption': report.missing_option,
            'missingImage': report.missing_image,
            'spellingMistake': report.spelling_mistake,
            'incorrectAnswer': report.incorrect_answer,
            'incorrectQuestion': report.incorrect_answer
        }
        if created:
            SUCCESS['Comments'] = 'Reported answer successfully.'
            return Response(SUCCESS, status=status.HTTP_201_CREATED)
        SUCCESS['Comments'] = 'Update answer report successfully'
        return Response(SUCCESS, status=status.HTTP_201_CREATED)

    @method_decorator(authorization_required)
    def put(self, request, *args, **kwargs):
        data = request.data
        answer_id = data.get('answerId')
        if not answer_id:
            raise serializers.ValidationError("answerId is required")
        report_keys = {
            'missingOption':'missing_option',
            'missingImage':'missing_image',
            'spellingMistake':'spelling_mistake',
            'incorrectAnswer':'incorrect_answer',
            'incorrectQuestion':'incorrect_question'
        }
        report_val = {
            'missing_option': False,
            'missing_image': False,
            'spelling_mistake': False,
            'incorrect_answer': False,
            'incorrect_question': False,
        }
        for key in data:
            if key in report_keys:
                if data[key]!='true':
                    raise serializers.ValidationError("Invalid {} value".format(key))
                report_val.update({report_keys[key]: True})
        if not report_val:
            raise serializers.ValidationError("At least one value should be true")

        report = AnswerReport.objects.filter(answer_id=answer_id,user=request.user)
        if report:
            report.update(**report_val)
            report = report.first()
            SUCCESS['Result'] = {
                'reportId': report.id,
                'missingOption': report.missing_option,
                'missingImage': report.missing_image,
                'spellingMistake': report.spelling_mistake,
                'incorrectAnswer': report.incorrect_answer,
                'incorrectQuestion': report.incorrect_answer
            }
            SUCCESS['Comments'] = 'Update answer report successfully'
            return Response(SUCCESS, status=status.HTTP_201_CREATED)
        FAIL['Comments'] = 'answer not found'
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)

class AnswerDetailView(APIView):

    @method_decorator(authorization_required)
    def get(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        answer_id = data.get("answerId")
        if not answer_id:
            raise serializers.ValidationError("answerId is required.")
        answer = Answer.objects.filter(id=answer_id).first()
        if answer:
            upvote_count = answer.answerupvote_set.all().count()
            reply_count = answer.answer_set.all().count()
            report_count = answer.answerreport_set.all().count()
            upvoted = AnswerUpvote.objects.filter(user=user, id=answer_id).exists()
            reported = AnswerReport.objects.filter(user=user, id=answer_id).exists()
            data = {
                'userId': answer.user.id,
                'userName': answer.user.get_full_name(),
                # 'userImage': answer.user.profile.image.url,
                'answerId': answer_id,
                'postId': answer.post.id,
                'text': answer.text,
                'image': '',
                'createdOn': naturaltime(answer.created_on),
                'updateOn': naturaltime(answer.updated_on),
                'upvoteCount': upvote_count,
                'reportCount': report_count,
                'replyCount': reply_count,
                'upvoted': upvoted,
                'reported': reported,
                'replies': []
            }
            if answer.image:
                data['image'] = answer.image.url
            if reported:
                report = AnswerReport.objects.filter(user=user, answer=answer)
                data['report'] = {
                    'reportId': report.id,
                    'missingOption': report.missing_option,
                    'missingImage': report.missing_image,
                    'spellingMistake': report.spelling_mistake,
                    'incorrectAnswer': report.incorrect_answer,
                    'incorrectQuestion': report.incorrect_answer
                }
            if reply_count > 0:
                for reply in answer.answer_set.all():
                    upvote_count = reply.answerupvote_set.all().count()
                    report_count = reply.answerreport_set.all().count()
                    upvoted = AnswerUpvote.objects.filter(answer=reply, user=request.user).exists()
                    r = {
                        'replyId': reply.id,
                        'userId': reply.user.id,
                        # 'userRole': reply.user.role.role,
                        'userName': reply.user.get_full_name(),
                        'text': reply.text,
                        'image': '',
                        'upvoteCount': upvote_count,
                        'reportCount': report_count,
                        'upvoted': upvoted,
                        'reported': reported
                    }
                    if reply.image:
                        r['image'] = reply.image.url
                    data['replies'].append(r)
            SUCCESS['Result'] = data
            return Response(SUCCESS, status=status.HTTP_200_OK)
        FAIL['Comments'] = "Answer not found"
        return Response(FAIL, status=status.HTTP_404_NOT_FOUND)