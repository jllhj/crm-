def initial_session(user,request):  # 分别用到views函数里面的user和request所以要把两个参数加进来 开始是不知道的粘贴过来才加
    # 方案一 信息太少 所以加了group表 和 action字段 来代替url 不用在页面上根据表名来取
    # permissions = user.roles.all().values('permissions__url').distinct()
    # # print(permissions)  # 把取到的queryset对象转换成列表格式 ['/users/','/users/add']
    # # print出来的是<QuerySet [{'permissions_url':'/users/'},{'permissions_url':'/users/add'}]>
    # permission_list = []
    # for item in permissions:
    #     permission_list.append(item['permissions__url'])
    #
    #
    # request.session['permission_list'] = permission_list

    # 方案二
    permissions = user.roles.all().values('permissions__url','permissions__group_id','permissions__action').distinct()
    permission_dict = {}
    for item in permissions:
        gid = item.get('permissions__group_id')
        if not gid in permission_dict:
            permission_dict[gid] = {
                'urls':[item['permissions__url'],],
                'actions':[item['permissions__action'],]

            }
        else:
            permission_dict[gid]['urls'].append(item['permissions__url'])
            permission_dict[gid]['actions'].append(item['permissions__action'])
    print(permission_dict)
    request.session['permission_dict'] = permission_dict

    # 注册菜单权限
    permissions = user.roles.all().values('permissions__url','permissions__action','permissions__title').distinct()
    print(permissions)
    menu_permission_list = []
    for item in permissions:
        if item['permissions__action'] == 'list':
            menu_permission_list.append((item['permissions__url'],item['permissions__title']))
    print('*'*120)
    print(menu_permission_list)
    request.session['menu_permission_list'] = menu_permission_list
