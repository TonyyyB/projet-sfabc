from django.db import models

# Create your models here.
NOTES = {
    "1 étoile" : 1,
    "2 étoiles" : 2,
    "3 étoiles" : 3,
    "4 étoiles" : 4,
    "5 étoiles" : 5,
}

class Note(models.Model):
    id_note = models.AutoField(primary_key=True)
    pseudonyme = models.CharField(max_length=100)
    valeur = models.IntegerField(max_length=1, choices=NOTES)
    message = models.CharField()