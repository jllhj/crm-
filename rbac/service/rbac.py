from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render,HttpResponse,redirect
import re
class ValidPermission(MiddlewareMixin):
    def process_request(self,request): # wsgi   在 中间件前面 需要加request请求信息
        current_path = request.path_info
        #  检查白名单
        valid_url_list = ['/login/','/reg/','/admin/.*',"/stark/rbac/.*"]
        for valid_url in valid_url_list:
            ret = re.match(valid_url,current_path)
            if ret:
                return None  # 通关return none return none→url.py→views.py→视图网页

        # 校验是否登录
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('/login/')




        # # 校验权限一
        # permission_list = request.session.get('permission_list',[])
        # current_path = request.path_info
        # # if current_path in permission_list: 不能这么写 因为列表里编辑删除的URL是正则匹配的 直接in 定死了
        #
        # for permission in permission_list:
        #     permission = '^%s$' % permission
        #
        #     ret = re.match(permission, current_path)
        #
        #     if ret:
        #         return None
        #
        # return HttpResponse('你没有访问权限')

        permission_dict = request.session.get('permission_dict')
        current_path = request.path_info
        for item in permission_dict.values():  # values只去他的值  {1: {'urls': ['/users/', '/users/add', '/users/delete/(\\d+)', '/users/edit/(\\d+)'], 'actions': ['list', 'add', 'delete', 'edit']}, 2: {'urls': ['/roles/'], 'actions': ['list']}}
            urls = item['urls']
            for reg in urls:
                reg = '^%s$'%reg
                print(reg)
                ret = re.match(reg,current_path)
                if ret:
                    request.actions = item['actions']
                    return None

        return HttpResponse('你没有访问权限')
