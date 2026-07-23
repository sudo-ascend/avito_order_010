import json
from collections import Counter
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from django.conf import settings
from django.shortcuts import render


DATA_FILE = settings.BASE_DIR / 'catalog' / 'data' / 'products.json'


def _format_price(value):
    try:
        amount = int(round(float(value)))
    except (TypeError, ValueError):
        return 'По запросу'

    return f"{amount:,}".replace(',', ' ') + ' ₽'


def _shorten(text, limit=140):
    cleaned = ' '.join((text or '').split())
    if len(cleaned) <= limit:
        return cleaned

    truncated = cleaned[: limit - 1].rsplit(' ', 1)[0]
    return f'{truncated}…'


def _static_image_path(local_path):
    normalized = (local_path or '').replace('\\', '/')
    if normalized.startswith('images/'):
        normalized = normalized[len('images/'):]
    return f'catalog/assets/images/products/{normalized}'


@lru_cache(maxsize=1)
def _load_catalog_payload():
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))


def _decorate_product(raw_product):
    images = []
    for image in raw_product.get('images', []):
        local_path = image.get('local_path')
        if not local_path:
            continue
        images.append(
            {
                'position': image.get('position', 0),
                'static_path': _static_image_path(local_path),
            }
        )

    title = (raw_product.get('title') or '').strip()
    description = raw_product.get('description') or raw_product.get('contents') or title
    available_quantity = raw_product.get('available_quantity') or 0

    return {
        'nm_id': raw_product.get('nm_id'),
        'title': title,
        'category': (raw_product.get('category') or 'Каталог').strip(),
        'category_parent': (raw_product.get('category_parent') or '').strip(),
        'description': _shorten(description),
        'price_current': raw_product.get('price_current'),
        'price_original': raw_product.get('price_original'),
        'price_current_display': _format_price(raw_product.get('price_current')),
        'price_original_display': _format_price(raw_product.get('price_original')),
        'discount_percent': raw_product.get('discount_percent') or 0,
        'available_quantity': available_quantity,
        'stock_display': f'В наличии: {available_quantity}' if available_quantity else 'Количество уточняется',
        'photo_count': raw_product.get('photo_count') or len(images),
        'reviews_count': raw_product.get('reviews_count') or 0,
        'rating': raw_product.get('review_rating') or raw_product.get('rating') or 0,
        'supplier_name': (raw_product.get('supplier_name') or '').strip(),
        'card_url': raw_product.get('card_url'),
        'images': images,
        'main_image': images[0]['static_path'] if images else 'catalog/assets/images/logo-circle.webp',
    }


def _build_featured_products(products, limit=6):
    featured = []
    used_categories = set()

    for product in products:
        if product['category'] in used_categories:
            continue
        featured.append(product)
        used_categories.add(product['category'])
        if len(featured) == limit:
            return featured

    for product in products:
        if product in featured:
            continue
        featured.append(product)
        if len(featured) == limit:
            break

    return featured


def index(request):
    payload = _load_catalog_payload()
    products = [_decorate_product(product) for product in payload.get('products', [])]
    featured_products = _build_featured_products(products)
    hero_product = featured_products[0] if featured_products else None
    gift_cards = featured_products[:6]

    category_counter = Counter(product['category'] for product in products)
    category_examples = {}
    for product in products:
        category_examples.setdefault(product['category'], product)

    categories = [
        {
            'name': category_name,
            'count': count,
            'image': category_examples[category_name]['main_image'],
            'sample': category_examples[category_name]['title'],
        }
        for category_name, count in category_counter.most_common()
    ]

    gallery_images = []
    for product in products:
        gallery_images.append(
            {
                'src': product['main_image'],
                'alt': product['title'],
                'category': product['category'],
            }
        )
        if len(gallery_images) == 8:
            break

    raw_timestamp = payload.get('fetched_at_utc')
    if not raw_timestamp and payload.get('products'):
        raw_timestamp = payload['products'][0].get('fetched_at_utc')

    fetched_at_display = ''
    if raw_timestamp:
        fetched_at_display = (
            datetime.fromisoformat(raw_timestamp)
            .astimezone(ZoneInfo('Europe/Moscow'))
            .strftime('%d.%m.%Y')
        )

    brand_name = next(
        (
            product['supplier_name']
            for product in products
            if product.get('supplier_name')
        ),
        'Подари момент',
    )

    context = {
        'brand_name': brand_name,
        'products': products,
        'hero_product': hero_product,
        'gift_cards': gift_cards,
        'featured_products': featured_products,
        'categories': categories,
        'gallery_images': gallery_images,
        'footer_categories': categories[:6],
        'seller_id': payload.get('seller_id'),
        'seller_url': payload.get('source_url'),
        'fetched_at_display': fetched_at_display,
        'stats': [
            {'value': payload.get('products_count', len(products)), 'label': 'товаров в выгрузке'},
            {'value': len(categories), 'label': 'категорий'},
            {'value': sum(product['photo_count'] for product in products), 'label': 'локальных фото'},
            {'value': max((product['discount_percent'] for product in products), default=0), 'label': 'макс. скидка, %'},
        ],
        'next_stage_items': [
            'Подключить форму заявки и обработку отправки без временных заглушек.',
            'Развернуть полноценный каталог и детальные страницы товаров.',
            'Добавить контентные блоки из следующего этапа ТЗ после согласования.',
        ],
        'current_year': 2026,
    }
    return render(request, 'catalog/index.html', context)
