from django.http import FileResponse


def generate_wishlist_file(ingredients):
    wishlist = '\n'.join([
        f'{ingredient["ingredient__name"]}:'
        f'{ingredient["total_sum"]}'
        f'{ingredient["ingredient__measurement_unit"]}.'
        for ingredient in ingredients
    ])

    response = FileResponse(wishlist, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=wishlist.txt'

    return response
