from django.conf.urls import url
from django.shortcuts import HttpResponse,render,redirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from stark.utils.mypage import Page
from django.db.models import Q
from django.db.models.fields.related import ForeignKey,ManyToManyField

class ShowList(object):  # showlist = ShowList(self) 这边要接收  还有下面有调用data_list也要传进来
    def __init__(self,config,data_list,request):
        self.config =config
        self.data_list = data_list
        self.request = request
        # 分页
        data_count = self.data_list.count()
        current_page = int(self.request.GET.get('page',1))
        base_path = self.request.path
        self.page = Page(current_page,data_count,base_path,self.request.GET,per_page=11,max_page=4)
        # 最重要
        self.page_data = self.data_list[self.page.start:self.page.end]

        # actions
        self.actions = self.config.new_actions()

    def get_action_list(self):
        temp= []
        for action in self.actions:
            temp.append({
                'name': action.__name__,
                'desc': action.short_description
            })
        return temp




    def get_filter_linktags(self):
        # print('list_filter:',self.config.list_filter)
        # link_dic = {}
        # import copy
        #
        # for filter_field in self.config.list_filter:  # ['publish','authors']
        #     # 放里面不会出现除了第一个字段 后面叠加 就是你request.get变成路由（字符串），但你还要用他字典取值
        #     params = copy.deepcopy(self.request.GET)
        #     # 拿到的是字符串
        #     cid = self.request.GET.get(filter_field,0)
        #     print(filter_field) # 'publish'
        #     filter_field_obj = self.config.model._meta.get_field(filter_field)
        #     print(type(filter_field_obj))
        #
        #     # print('rel....',filter_field_obj.rel.to.objects.all())
        #
        #     data_list = filter_field_obj.rel.to.objects.all()  # [<Publish: 苹果出版社>, <Publish: 香蕉出版社>]>     <QuerySet [<Author: alex>, <Author: egon>]>
        #     temp = []
        #
        #     if params.get(filter_field):
        #         del params[filter_field]
        #         temp.append('<a href="?%s">全部</a>'%params.urlencode())
        #     else:
        #         temp.append('<a href="#">全部</a>' )
        #
        #     for obj in data_list:
        #         # 如果Publish重了改值 如果另一个字段则加上
        #         params[filter_field] = obj.pk
        #         _url = params.urlencode()
        #         # 拿到的是字符串所以要int
        #         if int(cid) == obj.pk:
        #             link_tag = "<a class='active' href='?%s'>%s</a>"%(_url, str(obj))
        #         else:
        #             link_tag = "<a  href='?%s'>%s</a>" % (_url, str(obj))
        #         temp.append(link_tag)
        #         link_dic[filter_field] = temp
        # return link_dic
        import copy
        link_dic = {}
        for filter_field in self.config.list_filter:
            params = copy.deepcopy(self.request.GET)
            cid = self.request.GET.get(filter_field,0)
            filter_field_obj = self.config.model._meta.get_field(filter_field)
            data_list = filter_field_obj.rel.to.objects.all()
            temp =[]
            for obj in data_list:
                params[filter_field] = obj.pk
                _url = params.urlencode()
                if int(cid) == obj.pk:
                    link_tags = '<a class="active" href="?%s">%s</a>'%(_url,str(obj))
                else:
                    link_tags = '<a  href="?%s">%s</a>' % (_url, str(obj))
                temp.append(link_tags)
                link_dic[filter_field] = temp
        return link_dic



    def get_header(self):
        # 表头
        head_list = []
        print('header',self.config.new_list_display())
        for field in self.config.new_list_display():
            if callable(field):
                # head_list.append(field.__name__)
                val = field(self.config, header=True)
                head_list.append(val)
            else:
                if field == '__str__':
                    head_list.append(self.config.model._meta.model_name.upper())
                else:
                    #  表默认表中的数据变成中文的
                    val = self.config.model._meta.get_field(field).verbose_name
                    head_list.append(val)
        return head_list

    def get_body(self):
        # 表单数据

        print(self.config.list_display)  # 如果有定制类就用定制类display 如果没有就[] 最上面配置了
        new_data_list = []
        # [
        #
        #               ]
        for obj in self.page_data:  # [obj.name,obj.age],[obj1.name,obj.name2]
            temp = []
            # 每张表的配置类对象都不同 不能直接obj.name 别的表的对应的属性不同
            for field in self.config.new_list_display():
                # 不能直接对象.字符串 应该先反射
                if callable(field):
                    val = field(self.config, obj)  # 传obj是因为 需要编辑页面拿到对象的Pk值
                else:
                    try:
                        # 取__str__时候这段代码报错
                        field_obj = self.config.model._meta.get_field(field)
                        # 如果是多对多字段
                        if isinstance(field_obj,ManyToManyField):
                            ret = getattr(obj,field).all()
                            t = []
                            for mobj in ret:
                                t.append(str(mobj))

                            val = ','.join(t)
                            print('*' * 10, val)
                        else:
                            if field_obj.choices: # 如果字段对象里有choice 让他取后面的值
                                val = getattr(obj, 'get_'+field+'_display')
                            else:
                                val = getattr(obj, field)
                            if field in self.config.list_display_links:
                                _url = self.config.get_change_url(obj)
                                val = mark_safe("<a href='%s'>%s</a>" % (_url, val))
                    except Exception as e:
                        val = getattr(obj, field)

                temp.append(val)
            new_data_list.append(temp)
        return new_data_list

class ModelStark(object):   # 如果不把代码搬到里面 完全没有配置类可言
    list_display = ['__str__',]  # 配置类下面有list_display 默认类没有默认为空 调用时候返回默认类名字在temp里
    list_display_links = []
    modelform_class = None
    search_fields = []
    actions = []
    list_filter = []


    def __init__(self,model,site):
        self.model = model
        self.site =site

    def patch_delete(self,request,queryset):
        queryset.delete()
    patch_delete.short_description = '批量化删除'

    def new_actions(self):
        temp = []
        temp.append(ModelStark.patch_delete)
        temp.extend(self.actions)
        return temp

    def edit(self,obj=None,header=False):
        if header:
            return '操作'

        _url = self.get_change_url(obj)
        return mark_safe('<a href="%s">编辑</a>'%_url)

    def deletes(self,obj=None,header=False):
        if header:
            return '操作'

        _url = self.get_delete_url()
        return mark_safe('<a class="del" id="%s">删除</a>'%obj.pk)

    def checkbox(self,obj=None,header=False):
        if header:
            return mark_safe('<input id="choice" type="checkbox">')
        return mark_safe('<input class="item" type="checkbox" name="selected_pk" value="%s">'%obj.pk)

    def new_list_display(self):
        
        temp = []
        temp.append(ModelStark.checkbox)
        temp.extend(self.list_display)
        if not self.list_display_links:
            temp.append(ModelStark.edit)
        temp.append(ModelStark.deletes)
        return temp



    def get_change_url(self,obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        return reverse('%s_%s_change' % (app_label, model_name), args=(obj.pk,)) #  反向解析 edit需要传参数

    def get_add_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        return reverse('%s_%s_add' % (app_label, model_name))

    def get_delete_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        return reverse('%s_%s_delete' % (app_label, model_name))  #反向解析 edit需要传参数

    def get_list_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        return reverse('%s_%s_list' % (app_label, model_name))

    def get_modelform_class(self):

        if not self.modelform_class:  # 如果没有配置modelform
            from django.forms import ModelForm
            class ModelFormDemo(ModelForm):
                class Meta:
                    model = self.model
                    fields = '__all__'
            return ModelFormDemo
        else:
            return self.modelform_class


    def add_view(self,request):  # 接受popURL的值

        ModelFormDemo = self.get_modelform_class()

        form = ModelFormDemo()
        for bfield in form:
            print(type(bfield))
            from django.forms.boundfield import BoundField
            print(type(bfield.field)) # 字段对象
            from django.forms.models import ModelChoiceField
            if isinstance(bfield.field,ModelChoiceField): # 判断是否是choice字段,给浏览器加+号用的
                bfield.is_pop = True   # 一个对象点.一个值 以后就可以点.这个属性
                print(bfield.field.queryset.model) # 一对多或者多对多字段的关联模型表
                related_model_name = bfield.field.queryset.model._meta.model_name
                related_app_label = bfield.field.queryset.model._meta.app_label
                _url = reverse('%s_%s_add'%(related_app_label,related_model_name))
                # 给+号添加url用的并且提供id
                bfield.url = _url+'?pop_res_id=id_%s'%bfield.name


        if request.method == 'POST':
            form = ModelFormDemo(request.POST)
            if form.is_valid():
                obj = form.save()
                pop_res_id = request.GET.get('pop_res_id')
                if pop_res_id: # pop页面出来的
                    res = {'pk':obj.pk,'text':str(obj),'pop_res_id':pop_res_id}

                    return render(request,'pop.html',{'res':res})
                else: # 如果用户是自己输入网页添加的话 返回查看页面
                    return redirect(self.get_list_url())


        return render(request,'add_view.html',locals())

    def delete_view(self,request):
        if request.method == 'POST':
            id=request.POST.get("id")
            self.model.objects.get(pk=id).delete()
            return HttpResponse('OK')
        return redirect(self.get_list_url())

    def change_view(self,request,id):
        ModelFormDemo = self.get_modelform_class()
        edit_obj = self.model.objects.filter(pk=id).first()
        form = ModelFormDemo(instance=edit_obj)
        for bfield in form:
            print(type(bfield))
            from django.forms.boundfield import BoundField
            print(type(bfield.field))  # 字段对象
            from django.forms.models import ModelChoiceField
            if isinstance(bfield.field, ModelChoiceField):  # 判断是否是choice字段,给浏览器加+号用的
                bfield.is_pop = True  # 一个对象点.一个值 以后就可以点.这个属性
                print(bfield.field.queryset.model)  # 一对多或者多对多字段的关联模型表
                related_model_name = bfield.field.queryset.model._meta.model_name
                related_app_label = bfield.field.queryset.model._meta.app_label
                _url = reverse('%s_%s_add' % (related_app_label, related_model_name))
                # 给+号添加url用的并且提供id
                bfield.url = _url + '?pop_res_id=id_%s' % bfield.name

        if request.method == 'POST':
            form = ModelFormDemo(request.POST, instance=edit_obj)
            if form.is_valid():
                obj = form.save()
                pop_res_id = request.GET.get('pop_res_id')
                if pop_res_id:  # pop页面出来的
                    res = {'pk': obj.pk, 'text': str(obj), 'pop_res_id': pop_res_id}

                    return render(request, 'pop.html', {'res': res})
                else:
                    return redirect(self.get_list_url())
            return render(request, 'edit_view.html', locals())

        return render(request, 'edit_view.html', locals())






    def get_search_connection(self,request):

        key_word = request.GET.get('q','') # 当主业的时候 框里面才不会显示None
        self.key_word = key_word
        search_connection = Q()
        if key_word:
            # self.search_field # ['title','price']

            search_connection.connector = 'or'
            for search_field in self.search_fields:
                # 不能 直接在filter(search_field=key_word) 因为for循环结果是字符串 filter里面是变量=xxx
                # 这是写死的 data_list = self.model.objects.all().filter(Q(title=key_world)|Q(price=key_world)) # [obj1,obj2，obj....]   [['alex','32'],['egon','22']]
                search_connection.children.append((search_field + '__contains', key_word))  # +__contains 模糊查询
        return search_connection

    def get_filter_connection(self,request):
    #     filter_connection = Q()
    #     # 默认且 不用or
    #     for filter_field,val in request.GET.items():
    #         # 你传的键跟值 在list_filter表上才帮你过滤 如果没有这条件page键也会加进来导致报错
    #         if filter_field in self.list_filter:
    #             filter_connection.children.append((filter_field,val))
    #     return filter_connection

        filter_connection = Q()
        for filter_field,val in request.GET.items():
            if filter_field != 'page':
                filter_connection.children.append((filter_field,val))
        return  filter_connection

    def list_view(self,request):
        if request.method == 'POST': # action
            print('action',request.POST) # {'action': ['patch_init'], 'selected_pk': ['1']}>
            action = request.POST.get('action') # 获得select标签name = action 的 value值
            selected_pk = request.POST.getlist('selected_pk')
            action_func = getattr(self,action)  # 得到该名字的函数

            queryset = self.model.objects.filter(pk__in=selected_pk)
            action_func(request,queryset) # 使用函数 传request跟勾中的对象

        # 获取search的Q对象
        search_connection = self.get_search_connection(request)

        # 获取filter构建Q对象
        filter_connection = self.get_filter_connection(request)


        # 筛选获取当前表所有的数据
        data_list = self.model.objects.all().filter(search_connection).filter(filter_connection)

        # 按这showList展示页面
        showlist =ShowList(self,data_list,request)








        # for field in self.list_display: # self.list_display ["title','price']
        del_url = self.get_delete_url()
        add_url = self.get_add_url()
        return render(request,'list_view.html',locals())

    def extra_url(self):
        return []

    def get_url2(self):
        temp = []
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        temp.append(url(r'^add/', self.add_view, name='%s_%s_add' % (app_label, model_name)))
        temp.append(url(r'^/delete/', self.delete_view, name='%s_%s_delete' % (app_label, model_name)))
        temp.append(url(r'^(\d+)/change/', self.change_view, name='%s_%s_change' % (app_label, model_name)))
        temp.append(url(r'^$', self.list_view, name='%s_%s_list' % (app_label, model_name)))

        temp.extend(self.extra_url()) # extend空列表等于什么都没有做
        return temp

    @property
    def urls2(self):
        return self.get_url2(),None,None


class StarkSite(object):
    def __init__(self):
        self._registry = {}

    def register(self,model,stark_class=None):
        if not stark_class:
            stark_class = ModelStark

        self._registry[model] = stark_class(model,self)



    def get_url(self):
        temp = []
        for model,stark_class_obj in self._registry.items():
            model_name = model._meta.model_name
            app_label = model._meta.app_label
            # 分发url增删改查
            temp.append(url(r'^%s/%s/'%(app_label,model_name),stark_class_obj.urls2))
        return temp

    @property
    def urls(self):
        return self.get_url(),None,None


site = StarkSite()