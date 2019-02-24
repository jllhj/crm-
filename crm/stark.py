from stark.service.stark import site,ModelStark
from django.utils.safestring import mark_safe
from .models import *
from django.conf.urls import url
from django.shortcuts import redirect,HttpResponse,render
from django.http import JsonResponse

site.register(School)

class UserConfig(ModelStark):
    list_display = ['name','email','depart']
site.register(UserInfo,UserConfig)
class ClassConfig(ModelStark):
    def display_classname(self,obj=None,header=False):
        if header:
            return '班级名称'
        return '%s(%s)'%(obj.course.name,str(obj.semester))
    list_display = [display_classname,'tutor','teachers']

site.register(ClassList,ClassConfig)
class CustomerConfig(ModelStark):
    def display_gender(self,obj=None,header=False):
        if header:
            return '性别'
        return obj.get_gender_display()

    def display_course(self,obj=None,header=False):
        if header:
            return '咨询课程'
        temp = []
        for course in obj.course.all():
            s = '<a href="/stark/crm/customer/cancel_course/%s/%s" style="border:1px solid #369;padding:3px 6px"><span>%s</span></a>&nbsp;'%(obj.pk,course.pk,course.name) # 客户对象.pk 课程.pk
            temp.append(s)
        return mark_safe(''.join(temp))

    list_display = ['name',display_gender,'consultant',display_course]

    def cancel_course(self,request,customer_id,course_id):
        obj = Customer.objects.filter(pk=customer_id).first()
        obj.course.remove(course_id)
        return redirect(self.get_list_url())

    def public_customer(self,request):

        from django.db.models import Q
        import datetime
        now = datetime.datetime.now()
        # datetime.timedelta(days=3)
        delta_day3 = datetime.timedelta(days=3)
        delta_day15 = datetime.timedelta(days=15)
        # 未报名 且三天未跟进或者15天未成单
        user_id = 5 # 2是吴三江的ID值 如果登录的话 request.session [user_id] 就能拿到
        customer_list = Customer.objects.filter(Q(last_consult_date__lt=now-delta_day3)|Q(recv_date__lt=now-delta_day15),status=2).exclude(consultant=user_id) # 既有键值对又有Q对象 键值对放在Q对象后面 exclude 不等于的意思
        print(customer_list)  # <QuerySet [<Customer: 小东北>, <Customer: 泰哥>]>
        return render(request,'public.html',locals())

    def further(self,request,customer_id):
        user_id = 3 # 模拟登陆 如果登录的话 request.session.get(user_id) 就能拿到
        import datetime
        from django.db.models import Q
        delta_day3 = datetime.timedelta(days=3)
        delta_day15 = datetime.timedelta(days=15)
        now = datetime.datetime.now()
        #  为客户更改课程顾问,和对应时间  又加了一个Q对象 因为如果两个人同时打开页面 不判断过滤的话 越慢选的人就变成他的了
        ret = Customer.objects.filter(pk=customer_id).filter(Q(last_consult_date__lt=now-delta_day3)|Q(recv_date__lt=now-delta_day15),status=2).exclude(consultant=user_id).update(consultant=user_id,recv_date=now,last_consult_date=now)
        if not ret:
            return HttpResponse('下手晚了,已经被跟进')
        CustomerDistrbute.objects.create(customer_id=customer_id,consultant_id=user_id,date=now,status=1)
        return HttpResponse('ok')


    def mycustomer(self,request):
        user_id = 2
        customer_distrbute_list = CustomerDistrbute.objects.filter(consultant=user_id)
        return render(request,'mycustomer.html',locals())

    def extra_url(self):
        temp = []
        temp.append(url(r'cancel_course/(\d+)/(\d+)',self.cancel_course))
        temp.append(url(r'public', self.public_customer))
        temp.append(url(r'further/(\d+)',self.further))
        temp.append(url(r'mycustomer/',self.mycustomer))

        return temp

site.register(Customer,CustomerConfig)
site.register(Department)
site.register(Course)

class ConsultConfig(ModelStark):
    list_display = ['customer','consultant','date','note']
site.register(ConsultRecord,ConsultConfig)

class CourseRecordConfig(ModelStark):

    # def display_score(self,obj=None,header=False):
    #     if header:
    #         return '成绩'
    #
    #     return obj.get_score_display()
    def patch_studyrecord(self,request,queryset):
        print(queryset) # <QuerySet [<CourseRecord: python基础班(9期) day94>, <CourseRecord: python基础班(9期) day95>]>
        temp = []
        for course_record in queryset:
            # 与course_record关联的班级对应的所有学生
            student_list = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            print('+++++',student_list)
            for student in student_list:
                obj = StudyRecord(student=student,course_record=course_record)
                temp.append(obj)

        StudyRecord.objects.bulk_create(temp)

    def record(self,obj=None,header=False):
        if header:
            return '学习记录'
        return mark_safe('<a href="/stark/crm/studyrecord/?course_record=%s">记录</a>'%obj.pk)

    def score(self,request,course_record_id):
        if request.method == 'POST':
            print(request.POST) # QueryDict: {'csrfmiddlewaretoken': ['8DKNFRGiaBZpBgpbLBS0tm2ucmeueN4UW3H0n3NnRrnT1mSpLfpBIOrOBPX66GYZ'], 'score_4': ['60'], 'homework_note_4': ['111'], 'score_5': ['70'], 'homework_note_5': ['222'], 'score_6': ['80'], 'homework_note_6': ['333']}>
            dic = {}
            for key,value in request.POST.items():
                if key == 'csrfmiddlewaretoken':
                    continue
                field,pk = key.rsplit('_',1)
                # dic = {1:{'homework_note':'',score:'90'},2:{'homework_note':'',score:'90'}}

                if pk in dic: # 判断pk值是否在 在的话往后面添加才不会被覆盖
                    dic[pk][field] = value
                else:
                    dic[pk] = {field:value}
            print('dic', dic)

            for pk,val in dic.items():
                StudyRecord.objects.filter(pk=pk).update(**val)
            return redirect(request.path)


        Study_record_list = StudyRecord.objects.filter(course_record=course_record_id)
        score_choices = StudyRecord.score_choices
        return render(request,'score.html',locals())

    def extra_url(self):
        temp = []
        temp.append(url(r'record_score/(\d+)',self.score))
        return temp

    def record_score(self,obj=None,header=False):
        if header:
            return '录入成绩'
        return mark_safe('<a href="record_score/%s">录入</a>'%obj.pk)






    actions = [patch_studyrecord,]
    patch_studyrecord.short_description= '批量生成学习记录'
    list_display = ['class_obj', 'day_num', 'teacher', record,record_score]
site.register(CourseRecord,CourseRecordConfig)


class StudyConfig(ModelStark):
    # def display_record(self,obj=None,header=False):
    #     if header:
    #         return '记录'
    #
    #     return obj.get_record_display()

    def patch_late(self,request,queryset):
        queryset.update(record='late')

    actions = [patch_late,]
    patch_late.short_description = '迟到'


    list_display = ['student','course_record','record','score']

site.register(StudyRecord,StudyConfig)

class StudentConfig(ModelStark):
    def score_view(self,request,student_id):
        if request.is_ajax():
            sid = request.GET.get('sid')
            cid = request.GET.get('cid')
            study_record_list = StudyRecord.objects.filter(student=sid, course_record__class_obj=cid)
            data_list = []
            for study_record in study_record_list:
                day_num = study_record.course_record.day_num
                score = study_record.score
                data_list.append(['day%s'%day_num,score])
            print(data_list)
            return JsonResponse(data_list,safe=False) # 如果序列化的不是字典 需要改过来


        else:
            student = Student.objects.filter(pk=student_id).first()
            class_list = student.class_list.all()  # 拿到所有班级对象 有的人报不止1个班
            return render(request,'score_view.html',locals())

    def extra_url(self):
        temp = []
        temp.append(url(r'score_view/(\d+)',self.score_view))
        return temp

    def score_show(self,obj=None,header=False):
        if header:
            return '查看成绩'
        return mark_safe('<a href="score_view/%s">查看成绩</a>'%obj.pk)
    list_display = ['customer','class_list',score_show]
    list_display_links = ['customer']
site.register(Student,StudentConfig)
site.register(CustomerDistrbute)