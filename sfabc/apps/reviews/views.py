from django.shortcuts import render
from django.db.models import Count
from apps.reviews.models import Note
from sortable_listview import SortableListView

# Create your views here.
class ReviewListView(SortableListView):
    model = Note
    template_name = "reviews/reviews.html"
    context_object_name = "reviews"
    allowed_sort_fields = {'note': {'default_direction': '','verbose_name': 'Note'},'published_date': {'default_direction': '-','verbose_name': 'Publié le'}}
    default_sort_field = 'published_date'
    template_name = 'list.html'

    def get_queryset(self):
        return Note.objects.filter(produit__icontains=self.kwargs['pk']).annotate(nb_produits=Count('produits_categorie'))
    
    def get_context_data(self, **kwargs):
        context = super(ReviewListView, self).get_context_data(**kwargs)
        context['title'] = "Avis"
        return context