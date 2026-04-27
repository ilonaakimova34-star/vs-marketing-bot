from django.shortcuts import render, get_object_or_404
from .models import Project, Skill, Experience

def home(request):
    projects = Project.objects.all()
    skills = Skill.objects.all()
    experience = Experience.objects.all()
    return render(request, 'projects/home.html', {
        'projects': projects,
        'skills': skills,
        'experience': experience,
    })

def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {
        'projects': projects,
    })

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'projects/project_detail.html', {
        'project': project,
    })
