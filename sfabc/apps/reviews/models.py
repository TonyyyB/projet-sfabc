from django.db import models

# Create your models here.
NOTES = {
    1 : "1",
    2 : "2",
    3 : "3",
    4 : "4",
    5 : "5"
}

class Note(models.Model):
    id_note = models.AutoField(primary_key=True)
    pseudonyme = models.CharField(max_length=100)
    valeur = models.IntegerField(choices=NOTES)
    message = models.CharField()

    def __str__(self):
        return f"{self.pseudonyme} : {self.valeur}"