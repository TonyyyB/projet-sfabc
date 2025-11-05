from apps.reviews.models import Avis
from sortable_listview import SortableListView

# Create your views here.
class ReviewListView(SortableListView):
    model = Avis
    template_name = "reviews/reviews.html"
    context_object_name = "reviews"
    allowed_sort_fields = {'valeur': {'default_direction': '-','verbose_name': 'Note'},'date': {'default_direction': '-','verbose_name': 'Publié le'}}
    default_sort_field = 'date'
    paginate_by = 5