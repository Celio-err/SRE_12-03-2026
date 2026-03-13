from django.db import models
from django import forms


# Create your models here.
class Estudante(models.Model):
    GENERO_CHOICES = [
        ('M', 'Mane'),
        ('F', 'Feto'),
        ]
    
    DEPARTAMENTO_CHOICES = [
        ('', 'Hili Departamentu...'),
        ('Geologia_Petroleo', 'Geologia e Petroleo'),
        ('Engenharia_Civil', 'Engenharia Civil'),
        ('Engenharia_Mecanica', 'Engenharia Mecanica'),
        ('Engenharia_Informatica', 'Engenharia Informatica'),
        ('Engenharia_Eleticidade_e_Eletronica', 'Engenharia Eleticidade e Eletronica'),
    ]

    naran = models.CharField(max_length=100)
    data_moris = models.DateField()
    idade = models.IntegerField(null=True, blank=True)
    sexu = models.CharField(max_length=1, choices=GENERO_CHOICES)
    enderesu = models.CharField(max_length=100)
    munisipiu = models.CharField(max_length=100)
    departamentu = models.CharField(max_length=50, choices=DEPARTAMENTO_CHOICES)
    eskola_anterior = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='foto_estudante/', null=True, blank=True)

    def __str__(self):
        return self.naran
    
class FormEstudante(forms.ModelForm):
    class Meta:
        model = Estudante
        fields = ['naran', 'data_moris', 'sexu', 'enderesu', 'munisipiu', 'departamentu', 'eskola_anterior', 'foto']

        widgets = {
            'data_moris': forms.DateInput(attrs={
                'type': 'date', # Membuat muncul kalender
                'onchange': 'calculateAge()',  
                 'class': 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none' # Memanggil fungsi JavaScript saat tanggal berubah
            }),
            'sexu': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none'
            }),
            
        }                    