import base64
from datetime import date
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from app.models import Estudante, FormEstudante
import csv
from django.http import HttpResponse
import io
import os
import zipfile
from django.utils.text import slugify
from django.db.models import Count, Q




# Create your views here.


def login_process(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah. Silakan coba lagi.')
    return render(request, 'index.html')

def logout_process(request):
    logout(request)
    return redirect('index')

@login_required(login_url='index')
def RejistuEstudante(request):
    if request.method == 'POST':
        form = FormEstudante(request.POST, request.FILES)
        # Ambil data gambar dari form
        image_data = request.POST.get('image_data')  # Pastikan field ini ada di form HTML kamu

        if form.is_valid():
            estudante = form.save(commit=False)

            # Proses penyimpanan gambar jika ada
            if image_data and ";base64," in image_data:
                try:
                    # Pisahkan header base64 dari datanya
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1] # Ambil ekstensi (jpg/png)
                    
                    # Beri nama file unik berdasarkan nama siswa dan tanggal
                    file_name = f"foto_{estudante.naran}_{date.today()}.{ext}"
                    
                    # Ubah teks base64 menjadi file asli
                    data = ContentFile(base64.b64decode(imgstr), name=file_name)
                    estudante.foto = data # Masukkan ke field 'foto' di Model
                except Exception as e:
                    print(f"Error proses foto: {e}")

            today = date.today()
            birth_date = estudante.data_moris
            idade = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            estudante.idade = idade
            estudante.save()

            return redirect('dashboard')
    else:
        form = FormEstudante()
    return render(request, 'rejistu_estudante.html', {'form': form})

@login_required(login_url='index')
def edit_estudante(request, pk):
    estudante_obj = get_object_or_404(Estudante, pk=pk)

    if request.method == 'POST':        
        form = FormEstudante(request.POST, request.FILES, instance=estudante_obj)

        image_data = request.POST.get('image_data')  # Pastikan field ini ada di form HTML kamu

        if form.is_valid():
            est = form.save(commit=False)

            if image_data and ";base64," in image_data:
                try:
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    file_name = f"foto_{est.naran}_{date.today()}.{ext}"
                    data = ContentFile(base64.b64decode(imgstr), name=file_name)
                    est.foto = data
                except Exception as e:
                    print(f"Erru iha prosesa foto: {e}")

            today = date.today()
            birth_date = est.data_moris
            est.idade = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            est.save()
            return redirect('dashboard')
    else:
        form = FormEstudante(instance=estudante_obj)

    return render(request, 'rejistu_estudante.html', {
        'form': form, 
        'edit_mode': True})

@login_required(login_url='index')
def delete_estudante(request, pk):
    estudante = Estudante.objects.get(pk=pk)
    estudante.delete()
    return redirect('dashboard')

def index(request):
    return render(request, 'index.html')

@never_cache
@login_required(login_url='index')
def dashboard(request):
    # ---- Table: newest first, search by name or department ----
    estudante = Estudante.objects.all().order_by('-id')

    search_query = (request.GET.get('search') or '').strip()
    if search_query:
        estudante = estudante.filter(
            Q(naran__icontains=search_query) | Q(departamentu__icontains=search_query)
        )

    page_obj = Paginator(estudante, 10).get_page(request.GET.get('page'))

    # ---- KPI cards: one query instead of three ----
    totals = Estudante.objects.aggregate(
        total=Count('id'),
        mane=Count('id', filter=Q(sexu='M')),
        feto=Count('id', filter=Q(sexu='F')),
    )

    # ---- Department chart: students per department, split by gender ----
    rows = (
        Estudante.objects
        .values('departamentu')
        .annotate(
            mane=Count('id', filter=Q(sexu='M')),
            feto=Count('id', filter=Q(sexu='F')),
        )
    )

    # Merge blank/NULL departments into one "N/A" bar
    merged = {}
    for r in rows:
        name = (r['departamentu'] or '').strip() or 'N/A'
        d = merged.setdefault(name, {'departamentu': name, 'mane': 0, 'feto': 0})
        d['mane'] += r['mane']
        d['feto'] += r['feto']

    departamentu_stats = sorted(
        merged.values(), key=lambda d: d['mane'] + d['feto'], reverse=True
    )

    # ---- Munisipiu charts: students per municipality ----
    mun_rows = (
        Estudante.objects
        .values('munisipiu')
        .annotate(total=Count('id'))
    )

    merged_mun = {}
    for r in mun_rows:
        name = (r['munisipiu'] or '').strip() or 'N/A'
        merged_mun[name] = merged_mun.get(name, 0) + r['total']

    munisipiu_stats = [
        {'munisipiu': n, 'total': t}
        for n, t in sorted(merged_mun.items(), key=lambda x: x[1], reverse=True)
    ]

    context = {
        'total_estudante': totals['total'],
        'total_mane': totals['mane'],
        'total_feto': totals['feto'],
        'departamentu_stats': departamentu_stats,   # feeds the department chart
        'munisipiu_stats': munisipiu_stats,         # feeds the two munisipiu charts
        'estudante': page_obj,
    }
    return render(request, 'dashboard.html', context)

@never_cache
@login_required(login_url='index')
def print_todos_kartaun(request):
    queryset = Estudante.objects.all().order_by('-id')

    search_query = request.GET.get('search')
    if search_query:
        queryset = queryset.filter(naran__icontains=search_query)

    return render(request, 'print_kartaun.html', {
        'estudantes': queryset,
    })

def kartaun_estudante(request, pk):
    estudante = get_object_or_404(Estudante, pk=pk)
    return render(request, 'kartaun.html', {'estudante': estudante})