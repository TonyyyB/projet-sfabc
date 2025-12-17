from apps.reviews.models import Avis
from apps.products.models import Produit
from sortable_listview import SortableListView

# Create your views here.
class ReviewListView(SortableListView):
    model = Avis
    template_name = "reviews/reviews.html"
    context_object_name = "reviews"
    allowed_sort_fields = {'valeur': {'default_direction': '-','verbose_name': 'Note'},'date': {'default_direction': '-','verbose_name': 'Publié le'}}
    default_sort_field = 'valeur'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super(SortableListView,
                        self).get_context_data(**kwargs)
        context['current_sort_query'] = self.get_sort_string()
        context['current_querystring'] = self.get_querystring()
        context['sort_link_list'] = self.sort_link_list
        context['title'] = "Avis"
        context['produit'] = Produit.objects.filter(id_produit=self.kwargs['pk']).first()
        return context

    def get_queryset(self):
        qs = Avis.objects.filter(produit=self.kwargs['pk']).order_by(self.sort)
        return qs
