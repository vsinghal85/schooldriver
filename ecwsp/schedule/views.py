from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from ecwsp.sis.models import SchoolYear, Student
from .models import MarkingPeriod, Course, Period, CourseSection, CourseEnrollment
from .forms import EnrollForm

@user_passes_test(lambda u: u.groups.filter(name='faculty').count() > 0 or u.is_superuser)
def schedule(request):
    years = SchoolYear.objects.all().order_by('-start_date')[:3]
    mps = MarkingPeriod.objects.all().order_by('-start_date')[:12]
    periods = Period.objects.all()[:20]
    # TODO: remove this entire function?
    # jnm note: I'm not touching this because I don't think the following line
    # could have worked for a very long time
    courses = Course.objects.all().order_by('-startdate')[:20]

    if SchoolYear.objects.count() > 2: years.more = True
    if MarkingPeriod.objects.count() > 3: mps.more = True
    if Period.objects.count() > 6: periods.more = True
    if Course.objects.count() > 6: courses.more = True

    return render_to_response('schedule/schedule.html', {'request': request, 'years': years, 'mps': mps, 'periods': periods, 'courses': courses})


@user_passes_test(lambda u: u.groups.filter(name='faculty').count() > 0 or u.is_superuser)
def schedule_enroll(request, id):
    course = get_object_or_404(CourseSection, pk=id)
    if request.method == 'POST':
        form = EnrollForm(request.POST)
        if form.is_valid():
            CourseEnrollment.objects.filter(course_section=course).delete() # start afresh; only students passed in from the form should be enrolled
            # add manually select students first
            selected = form.cleaned_data['students']
            for student in selected:
                # add
                enroll, created = CourseEnrollment.objects.get_or_create(user=student, course_section=course)
                # left get_or_create in case another schedule_enroll() is running simultaneously
                if created: enroll.save()
            # add cohort students second
            cohorts = form.cleaned_data['cohorts']
            for cohort in cohorts:
                for student in cohort.student_set.all():
                    enroll, created = CourseEnrollment.objects.get_or_create(user=student, course_section=course)

            if 'save' in request.POST:
                return HttpResponseRedirect(reverse('admin:schedule_coursesection_change', args=[id]))

    students = Student.objects.filter(courseenrollment__course_section=course)
    form = EnrollForm(initial={'students': students})
    return render(request, 'schedule/enroll.html', {'request': request, 'form': form, 'course': course})
