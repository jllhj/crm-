'''
page_num目前页数    total_count显示总数   url_prefix当前路由 格式为:/路由/
per_page每页显示数量  max_page展示页数
view.py:
    page_obj=Page(page,total_count,url_prefix,per_page,max_page)
    ret = models.表.objects.all()[page_obj.start:page_obj.end]   #控制显示的表数据或内容数量
    page_html=page_obj.page_html()                               #HTML分页
    return render(request,"HTML",{"ret":ret,"page_html":page_html,})
HTML:
<nav>
    <ul class="pagination">
        {{ page_html|safe }}
    </ul>
</nav>
'''
import math
import copy
class Page():
    def __init__(self,page_num,total_count,url_prefix,requests,per_page,max_page):
        '''
        :param page_num: 当前页码数
        :param total_count: 数据总数
        :param url_prefix: a标签href的前缀
        :param requests 接收request.get请求字典来处理数据,让a标签保存改字典
        :param per_page: 每页显示多少条数据
        :param max_page: 页面上最多显示几个页码
        '''
        self.total_count=total_count
        self.url_prefix=url_prefix
        self.requests=copy.deepcopy(requests)
        self.per_page=per_page
        self.max_page=max_page
        total_page = math.ceil(total_count / per_page)
        self.total_page=total_page
        try:
            if total_page<1:
                total_page=1
            page_num = int(page_num)
            if page_num > total_page:
                page_num = total_page

        except Exception:
            page_num = 1
        self.page_num = page_num
        self.data_start = (page_num - 1) * self.per_page
        self.data_end = page_num *self.per_page
        if total_page < max_page:
            max_page = total_page
        half_max_page = max_page // 2
        page_start = page_num - half_max_page
        page_end = page_num + half_max_page
        if page_start <= 1:
            page_start = 1
            page_end = max_page

        if page_end >= total_page:
            page_end = total_page
            page_start = total_page - max_page + 1
        self.page_start=page_start
        self.page_end=page_end
        

    @property
    def start(self):
        return self.data_start

    @property
    def end(self):
        return self.data_end

    def page_html(self):
        #  自己拼接分页html代码
        html_str_list = []
        # 首页标签
        html_str_list.append('<li><a href="{}?page=1" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>'.format(self.url_prefix))
        if self.page_num > 1:
            # 上一页
            html_str_list.append("<li><a href='{}?page={}'><</a></li>".format(self.url_prefix,self.page_num - 1))
        else:
            # 如果已经是第一页了 给他不能点
            html_str_list.append("<li><a disabled><</a></li>")

        for i in range(self.page_start,self.page_end + 1):
            self.requests["page"]=i
            if i == self.page_num:
                tmp = "<li class='active' ><a href='{0}?{1}'>{2}</a></li>".format(self.url_prefix,self.requests.urlencode(),i)
            else:
                # self.requests.urlencode() 把{'page':'12','title_startswith':'py','id_gt':'5'} 转化成字符串'page=12&title_startswith=py&id_gt=5'
                tmp = "<li><a href='{0}?{1}'>{2}</a></li>".format(self.url_prefix,self.requests.urlencode(),i)
            html_str_list.append(tmp)
        if self.page_num < self.total_page:
            # 下一页
            html_str_list.append("<li><a href='{}?page={}'>></a></li>".format(self.url_prefix,self.page_num + 1))
        else:
            # 如果已经是最后一页了 不能点
            html_str_list.append("<li><a disabled>></a></li>")
        #  尾页标签
        html_str_list.append('<li><a href="{}?page={}" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>'.format(self.url_prefix,self.total_page))
        page_html = "".join(html_str_list)
        return page_html
