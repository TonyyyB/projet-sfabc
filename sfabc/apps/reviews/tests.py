from django.test import TestCase
from .models import Note

# Create your tests here.
class NoteModelTest(TestCase):
    def setUp(self):
        self.note = Note.objects.create(pseudonyme="test1", valeur=2, message="message test 1")
    
    def test_note_creation(self):
        self.assertEqual(self.note.pseudonyme, "test1")
        self.assertEqual(self.note.valeur,     2)
        self.assertEqual(self.note.message,    "message test 1")
    
    def test_string_repr(self):
        self.assertEqual(str(self.note), "test1 : 2")
    
    def test_note_updating(self):
        self.note.pseudonyme = "update test1"
        self.note.save()

        updated_note:Note = Note.objects.get(id_note=self.note.id_note)
        self.assertEqual(updated_note.pseudonyme, "update test1")
    
    def test_note_deletion(self):
        self.note.delete()
        self.assertEqual(Note.objects.count(), 0)