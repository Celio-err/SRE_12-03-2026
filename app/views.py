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
    estudante = Estudante.objects.all().order_by('-id')  # Mengambil semua data Estudante dan mengurutkannya berdasarkan ID secara menurun
   
    # Fitur pencarian berdasarkan nama atau departemen
    search_query = request.GET.get('search')
    if search_query:
        estudante = estudante.filter(naran__icontains=search_query) | estudante.filter(departamentu__icontains=search_query)

    paginator = Paginator(estudante, 20)  # Menampilkan 20 data per halaman

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Mengambil jumlah total data dari tabel Estudante
    total_estudante = Estudante.objects.count()
    # Mengambil jumlah total data berdasarkan jenis kelamin
    total_mane = Estudante.objects.filter(sexu='M').count()
    total_feto = Estudante.objects.filter(sexu='F').count()
    context = {
        'total_estudante': total_estudante, 
        'total_mane': total_mane,
        'total_feto': total_feto,
        'estudante': page_obj,
    }

    return render(request, 'dashboard.html', context)