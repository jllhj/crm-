from django import template
register = template.Library()



@register.inclusion_tag('menu.html')
def get_menu(request):
    # 获取当前用户可以放到菜单栏的权限
    menu_permission_list = request.session.get('menu_permission_list')
    return {'menu_permission_list':menu_permission_list}