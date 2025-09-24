from django.test import TestCase

# Exemple d'utilisation

# from sfabc.models import Animal


# class AnimalTestCase(TestCase):
#     def setUp(self):
#         Animal.objects.create(name="lion", sound="roar")
#         Animal.objects.create(name="cat", sound="meow")

#     def test_animals_can_speak(self):
#         """Animals that can speak are correctly identified"""
#         lion = Animal.objects.get(name="lion")
#         cat = Animal.objects.get(name="cat")
#         self.assertEqual(lion.speak(), 'The lion says "roar"')
#         self.assertEqual(cat.speak(), 'The cat says "meow"')

# Pour lancer les tests

# Run all the tests in the animals.tests module
# $ ./manage.py test sfabc.tests

# Run all the tests found within the 'animals' package
# $ ./manage.py test sfabc

# Run just one test case class
# $ ./manage.py test sfabc.tests.AnimalTestCase

# Run just one test method
# $ ./manage.py test sfabc.tests.AnimalTestCase.test_animals_can_speak