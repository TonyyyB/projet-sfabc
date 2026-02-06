from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from sortable_listview import SortableListView

from apps.products.models import Produit
from apps.reviews.models import Avis, Reponse

# Create your views here.
class ReviewListView(SortableListView):
    """TODO: Vérifier — Vue listant et triant les avis d'un produit (pagination incluse)."""
    model = Avis
    template_name = "reviews/reviews.html"
    context_object_name = "reviews"
    allowed_sort_fields = {
        "valeur": {"default_direction": "-", "verbose_name": "Note"},
        "date": {"default_direction": "-", "verbose_name": "Publié le"},
    }
    default_sort_field = "valeur"
    paginate_by = 5

    def get_context_data(self, **kwargs):
        """TODO: Vérifier — Ajoute au contexte les infos de tri/pagination et le produit concerné par les avis."""
        context = super().get_context_data(**kwargs)
        context['current_sort_query'] = self.get_sort_string()
        context['current_querystring'] = self.get_querystring()
        context['sort_link_list'] = self.sort_link_list
        context['title'] = "Avis"
        context['produit'] = Produit.objects.filter(id_produit=self.kwargs['pk']).first()
        return context

    def get_queryset(self):
        """TODO: Vérifier — Retourne les avis du produit (pk URL) triés selon le champ courant (sortable_listview)."""
        return Avis.objects.filter(produit=self.kwargs['pk']).order_by(self.sort)

def add_review(request, pk):
    """TODO: Vérifier — Crée un avis à partir du formulaire POST puis redirige vers le détail produit."""
    if request.method == "POST":
        produit = get_object_or_404(Produit, id_produit=pk)
        print(request.POST)
        Avis.objects.create(
            produit=produit,
            pseudonyme=request.POST.get("pseudonyme"),
            valeur=int(request.POST.get("stars")[0]),
            message=request.POST.get("message", ""),
        )

    return redirect("products:detail_produit", pk=pk)


def add_reply(request, pk, avis_id):
    """Crée une réponse à un avis (réservé aux superusers)."""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé")
    
    if request.method == "POST":
        avis = get_object_or_404(Avis, id_note=avis_id)
        
        # Vérifier que l'avis n'a pas déjà une réponse
        if avis.reponse is None:
            reponse = Reponse.objects.create(
                message=request.POST.get("message", ""),
            )
            avis.reponse = reponse
            avis.save()
    
    # Rediriger vers la page d'origine (détail produit ou liste avis)
    next_url = request.POST.get("next", "")
    if next_url:
        return redirect(next_url)
    return redirect("products:detail_produit", pk=pk)
