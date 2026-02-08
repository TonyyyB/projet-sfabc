from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect, render

from apps.products.models import Famille, Produit
from .models import Avis, Reponse


@login_required
def avis_list(request):
    """
    Liste des avis avec filtres et tri.
    
    Filtres disponibles:
    - Par produit
    - Par nombre d'avis (produits avec le plus d'avis)
    - Par date (avis les plus récents)
    """
    # Récupération des paramètres de filtre/tri
    filtre_produit = request.GET.get('produit', '')
    tri = request.GET.get('tri', 'recent')  # 'recent', 'avec_reponse', 'sans_reponse', 'produit', 'note'
    
    # Liste de toutes les familles avec leurs produits pour le filtre groupé
    familles = Famille.objects.prefetch_related('famille').order_by('nom_famille')
    
    # Base queryset
    avis_qs = Avis.objects.select_related('produit', 'produit__famille', 'reponse').all()
    
    # Filtre par produit
    if filtre_produit:
        avis_qs = avis_qs.filter(produit__id_produit=filtre_produit)
    
    # Tri / Filtre
    if tri == 'recent':
        avis_qs = avis_qs.order_by('-date', '-id_note')
    elif tri == 'produit':
        avis_qs = avis_qs.order_by('produit__nom_produit', '-date')
    elif tri == 'avec_reponse':
        # Filtrer uniquement les avis avec une réponse
        avis_qs = avis_qs.filter(reponse__isnull=False).order_by('-date', '-id_note')
    elif tri == 'sans_reponse':
        # Filtrer uniquement les avis sans réponse
        avis_qs = avis_qs.filter(reponse__isnull=True).order_by('-date', '-id_note')
    elif tri == 'note':
        avis_qs = avis_qs.order_by('-valeur', '-date')
    
    # Pagination
    paginator = Paginator(avis_qs, 10)  # 10 avis par page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistiques pour l'en-tête
    stats = {
        'total_avis': Avis.objects.count(),
        'avis_sans_reponse': Avis.objects.filter(reponse__isnull=True).count(),
        'avis_avec_reponse': Avis.objects.filter(reponse__isnull=False).count(),
    }
    
    # Produits avec leur nombre d'avis pour le résumé
    produits_stats = Produit.objects.annotate(
        nb_avis=Count('avis'),
        dernier_avis=Max('avis__date')
    ).filter(nb_avis__gt=0).order_by('-nb_avis')[:5]
    
    context = {
        'avis_list': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'familles': familles,
        'filtre_produit': filtre_produit,
        'tri': tri,
        'stats': stats,
        'produits_stats': produits_stats,
    }
    
    return render(request, 'admin/reviews/avis_list.html', context)


@login_required
def avis_repondre(request, pk):
    """Ajouter ou modifier une réponse à un avis."""
    avis = get_object_or_404(Avis, pk=pk)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        
        if not message:
            messages.error(request, "Le message de réponse ne peut pas être vide.")
            return redirect('admin_reviews:admin_avis_list')
        
        if avis.reponse:
            # Modifier la réponse existante
            avis.reponse.message = message
            avis.reponse.save()
            messages.success(request, "Réponse modifiée avec succès.")
        else:
            # Créer une nouvelle réponse
            reponse = Reponse.objects.create(message=message)
            avis.reponse = reponse
            avis.save()
            messages.success(request, "Réponse ajoutée avec succès.")
        
        return redirect('admin_reviews:admin_avis_list')
    
    # GET: afficher la page avec le formulaire de réponse
    context = {
        'avis': avis,
    }
    return render(request, 'admin/reviews/avis_repondre.html', context)


@login_required
def avis_delete(request, pk):
    """Supprimer un avis."""
    avis = get_object_or_404(Avis, pk=pk)
    
    if request.method == 'POST':
        # Supprimer la réponse associée si elle existe
        if avis.reponse:
            avis.reponse.delete()
        avis.delete()
        messages.success(request, "Avis supprimé avec succès.")
    
    return redirect('admin_reviews:admin_avis_list')


@login_required
def reponse_delete(request, pk):
    """Supprimer une réponse d'un avis."""
    reponse = get_object_or_404(Reponse, pk=pk)
    
    if request.method == 'POST':
        # Récupérer l'avis associé et retirer la référence
        avis = Avis.objects.filter(reponse=reponse).first()
        if avis:
            avis.reponse = None
            avis.save()
        reponse.delete()
        messages.success(request, "Réponse supprimée avec succès.")
    
    return redirect('admin_reviews:admin_avis_list')
