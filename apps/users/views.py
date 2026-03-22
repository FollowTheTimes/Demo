from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User

@login_required
def profile_view(request):
    """用户个人资料视图"""
    if request.method == 'POST':
        # 处理表单提交
        user = request.user
        user.phone = request.POST.get('phone', user.phone)
        user.gender = request.POST.get('gender', user.gender)
        user.birthday = request.POST.get('birthday', user.birthday)
        user.bio = request.POST.get('bio', user.bio)
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()
        messages.success(request, '个人资料更新成功！')
        return redirect('profile')
    return render(request, 'users/profile.html', {'user': request.user})
