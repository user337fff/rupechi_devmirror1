from apps.commons.models import ImageModel, WithBreadcrumbs, FullSlugMixin
from apps.seo.models import SeoBase
from ckeditor_uploader.fields import RichTextUploadingField
from django.apps import apps
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.http.response import Http404
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from slugify import slugify
from pprint import pprint as pp
from django.db.models import Q

from ..cache import CategoryCacheMixin
from ..filtering import ProductFilterSEF
from ...domains.middleware import get_request
from ...domains.models import Domain
from ...feedback.models import RecipientMixin

SLUG_PRICE = 'price'


class Catalog(MPTTModel, SeoBase, ImageModel, WithBreadcrumbs, CategoryCacheMixin):
	CATEGORY = 'category'
	ALIAS = 'alias'
	TYPE_CHOICES = (
		(CATEGORY, 'Категория'),
		(ALIAS, 'Алиас')
	)

	domain = models.ManyToManyField('domains.Domain', verbose_name="Домены", blank=True)
	receivers = models.ManyToManyField('feedback.Recipient', verbose_name='Email для уведомления о покупке в категории',
									   blank=True, null=True)
	parent = TreeForeignKey('self', verbose_name='Родительская категория',
							on_delete=models.CASCADE, blank=True,
							null=True, related_name='children')
	is_active = models.BooleanField(
		verbose_name='Активна', default=True, db_index=True)
	discount_category = models.ManyToManyField('domains.Domain', verbose_name='Не применять скидку для доменов',
											   blank=True, null=True, related_name='discount_category')
	is_import_active = models.BooleanField('В выгрузке', default=True)
	is_index = models.BooleanField('На главной', default=False)
	is_hide = models.BooleanField('Скрыт', default=False)
	
	# info
	title = models.CharField(
		verbose_name='Название (H1)', max_length=127, db_index=True)
	short_title = models.CharField('Краткое название', max_length=125, blank=True, default="")
	description = models.TextField(
		verbose_name='Описание', blank=True, default='')

	product_description = RichTextUploadingField('Описание для продукта', blank=True, default="",
												 help_text="||brand|| - Производитель")
	old_product_description = RichTextUploadingField('Описание для продукта', blank=True, default="",
												 help_text="||brand|| - Производитель")

	image = models.ImageField(verbose_name='Изображение',
							  upload_to='images/categories/',
							  blank=True, null=True)
	image_md5 = models.CharField(verbose_name='Хэш изображения', blank=True,
								 default='', max_length=63,
								 help_text='Заполняется автоматически')

	# import
	id_1c = models.UUIDField(
		verbose_name='Идентификатор 1С', blank=True, null=True,
		help_text='Заполняется автоматически')

	# extra seo settings
	seo_text = RichTextUploadingField(verbose_name='Текст',
									  default='', blank=True)
	seo_img = models.ImageField(verbose_name='Изображение',
								upload_to='images/categories/seo/', default='',
								blank=True)
	show_on_menu = models.BooleanField(verbose_name=u'Отображать в выбранных категориях', default=False)
	show_on_categories = models.ManyToManyField('self', verbose_name='Отображать в категориях', blank=True,
												null=True, related_name='category_selector')
	# dates
	created_at = models.DateTimeField(
		verbose_name='Дата создания', auto_now_add=True)
	updated_at = models.DateTimeField(
		verbose_name='Дата последнего обновления', auto_now=True)
	# attrs
	saved_attrs_children = models.BooleanField('Сохранить текущие атрибуты для дочерних категорий',
											   help_text="Обновляет дочерние категории каждый раз "
														 "когда сохраняется текущая категория", default=False)
	saved_attrs_parent = models.BooleanField('Получить атрибуты родительской категории',
											 help_text="Обновляет атрибуты", default=False)
	dont_save_attrs_parent = models.BooleanField('не получать атрибуты родителя',
												 help_text="Блокирует получение атрибутов от родительской категории",
												 default=False, blank=True)
	type = models.CharField('Тип', max_length=125, choices=TYPE_CHOICES)
	brands = models.ManyToManyField('catalog.Brand', verbose_name='Производители', symmetrical=False, blank=True)
	search = models.CharField('Поисковый запрос', max_length=125, blank=True, default="")
	hit_check_products = models.BooleanField('Определять хит по значку "Является хитом" в товаре', default=False)
	discount_brands = models.ManyToManyField('catalog.Brand', verbose_name="Без онлайн скидки", blank=True,
											 related_name='discount_categories')
	discount_brands_save_child = models.BooleanField('Сохранять бренды для детей', default=False)
	alias_products = models.ManyToManyField('catalog.Product', verbose_name="Продукты", blank=True,
											related_name='aliases')
	unlink_brand = models.BooleanField('Убрать ссылку с производителя', default=False)
	keywords = models.CharField('Ключевые слова', max_length=250, blank=True, default="")
	search_vector = SearchVectorField(null=True)
	visible_mounting = models.BooleanField('Показывать пункт монтаж', default=False)

	PAGINATE_PRODUCTS_BY = 30
	FPP_QUANTITY = PAGINATE_PRODUCTS_BY

	def replacer_tags(self):
		tags_replacer = {
			"<h1>": "<p class='element--h1'>",
			"</h1>": "</p>",

			"<b>": "<span class='element--b'>",
			"</b>": "</span>",

			"<u>": "<span class='element--u'>",
			"</u>": "</span>",

			"<i>": "<span class='element--i'>",
			"</i>": "</span>",

			"<em>": "<span class='element--em'>",
			"</em>": "</span>",

			"<strong>": "<span class='element--strong'>",
			"</strong>": "</span>"
		}
		seoTestList = self.seo.all()
		for seo in seoTestList:
			for k, v in tags_replacer.items():
				seo.meta_message = seo.meta_message.replace(k, v)
			seo.save()
		

	def __str__(self):
		return self.title

	def get_absolute_url(self, *args, **kwargs):
		domain = get_request().domain
		try:
			slug, _ = self.slugs.get_or_create(domain=domain, defaults={'slug': slugify(self.title)})
			return reverse('pages:page_detail', args=[slug.slug])
		except Exception as exception:
			print('*** HTTP EXCEPT 404', 'apps/catalog/models/category.py 105', exception)
			raise Http404
		return reverse('category', args=[self.encode_slug(domain=domain)])

	# def save(self, *args, **kwargs):
	# 	search_vector = (
	# 			SearchVector('title', weight='A')
	# 			+ SearchVector('keywords', weight='B')
	# 	)
	# 	# поисковой вектор можно обновлять только у уже существующих записей бд
	# 	try:
	# 		if not self.is_active:
	# 			print(f'=== DEACT DEBUG CAT ID {self.id_1c}')
	# 		if self.pk:
	# 			self.search_vector = search_vector
	# 			super().save(*args, **kwargs)
	# 		else:
	# 			_ = super().save(*args, **kwargs)
	# 			Category.objects.filter(pk=self.pk).update(search_vector=search_vector)
	# 			return _
	# 	except:
	# 		print(f'CAT-SAVE PROBLEM {args} {kwargs} {self.parent}')
	# 		pp(self.__dict__)
	# 		raise

	def get_recivers(self):
		return Category.objects.get(domain=self.domain, title=self.title, is_active=True).receivers.all()

	def get_breadcrumbs(self, **kwargs):
		filters = {}
		request = get_request()
		domain = request.domain
		if domain:
			filters['domain__exact'] = domain
		parents = [
			(parent.title, parent.get_absolute_url(domain))
			for parent in self.get_ancestors().filter(**filters)
		]
		return super().get_breadcrumbs(parents)

	def get_products(self):
		Product = apps.get_model('catalog.Product')
		if self.type == self.CATEGORY:
			products = Product.objects.active(
				category__in=self.get_descendants(include_self=True)).order_by('id')
			return products
		return Product.objects.active(id__in=self.alias_products.values_list('id', flat=True)).order_by('id')

	def update_attrs(self, items, attrs=None):
		"""Установка атрибутов для категорий"""
		attrs = attrs or self.attrs.all()
		bulk_items = []
		for category in items:
			for attr in attrs:
				bulk_items += [CategoryAttribute(category=category, attribute=attr.attribute, sort=attr.sort)]
		if bulk_items:
			CategoryAttribute.objects.bulk_create(bulk_items, ignore_conflicts=True)

	def update_brands_discount(self):
		"""Прокидывание брендов скидок детям"""
		brands = self.discount_brands.all()
		for category in self.get_children().iterator():
			print("Category", category)
			print(brands)
			category.discount_brands.add(*brands)

	@classmethod
	def get_catalog(cls, dicted=True):
		"""Получение списка категорий каталогом"""
		domain = get_request().domain
		categories = cls.objects \
			.filter(is_active=True, domain__exact=domain, level__lte=1) \
			.all().order_by('tree_id', 'lft')
		dict_categories = {}
		if dicted:
			dict_categories = cache.get(f'{domain}_cached_categories') or {}
			if not dict_categories:
				for category in categories:
					if category.parent and category.parent.domain.filter(
							domain=domain.domain).exists():
						items = dict_categories.get(category.parent, [])
						items += [category]
						dict_categories[category.parent] = items
					else:
						dict_categories[category] = []
				cache.set(f'{domain}_cached_categories', dict_categories, 10 * 60)
		return dict_categories, categories

	def get_related_categories(self):
		domain = get_request().domain
		show_aliases = Catalog.objects.filter(Q(show_on_menu=True) & Q(show_on_categories__pk=self.pk) & Q(domain=domain)\
											  & Q(is_active=True) & ~Q(parent__pk=self.pk))
		related_categories = list(self.get_children().filter(is_active=True, domain__exact=domain)\
			.exclude(Q(show_on_menu=True) & Q(parent__pk=self.pk))
		    .order_by('is_hide',
					  'tree_id',
					  'lft')) + list(show_aliases)
		return related_categories

	def get_key_slug(self, domain=None):
		class_name = self.__class__.__name__
		if class_name in ['Page', 'BasePage']:
			class_name = 'Page'
		return f"{domain.domain + '_' if domain else ''}{class_name}_{self.id}"

	class Meta:
		verbose_name = 'Каталог'
		verbose_name_plural = 'Каталог'


class CategoryManager(models.Manager):

	def get_queryset(self):
		return super(CategoryManager, self).get_queryset().filter(type=Catalog.CATEGORY)

# class DebugQS(QuerySet, CategoryManager):
#
# 	def update(self, **kwargs):
# 		if 'is_active' in kwargs.keys() and not kwargs['is_active']:
# 			# print('LOCALS ' + str(locals()))
# 			# print('DICT ' + str(self.__dict__))
# 			print(f'=== DEACT DEBUG UPDATE CAT IDs ' + str(list(self.values_list('id', flat=True))))
# 		return super().update(**kwargs)
#
# 	def update_or_create(self, defaults=None, **kwargs):
# 		try:
# 			debug_id = super(CategoryManager, self).update_or_create(defaults, **kwargs)
# 			if ('is_active' in kwargs.keys() and not kwargs['is_active']) or \
# 			(defaults and 'is_active' in defaults.keys() and not defaults['is_active']):
# 				print(f'=== DEACT DEBUG UPDATE_OR_CREATE CAT ID {debug_id[0].pk}')
# 			return debug_id
# 		except:
# 			print(f'DEBUGQS {args} {kwargs} {self.parent}')
# 			pp(self.__dict__)
# 			raise

class Category(Catalog):
	objects = CategoryManager()
	# objects = DebugQS.as_manager()

	class Meta:
		verbose_name = 'Категория'
		verbose_name_plural = 'Категории'
		proxy = True

	def save(self, *args, **kwargs):
		self.type = self.CATEGORY
		return super(Category, self).save(*args, **kwargs)

	def get_absolute_url(self, *args, **kwargs):
		domain = get_request().domain
		try:
			slug, _ = self.slugs.get_or_create(domain=domain, defaults={'slug': slugify(self.title)})
			return reverse('pages:page_detail', args=[slug.slug])
		except Exception as exception:
			print('404 generated', exception)
			raise Http404
		return reverse('category', args=[self.encode_slug(domain=domain)])

	def get_key_slug(self, domain=None):
		class_name = self.__class__.__name__
		if class_name in ['Page', 'BasePage']:
			class_name = 'Page'
		return f"{domain.domain + '_' if domain else ''}{class_name}_{self.id}"


class AliasManager(models.Manager):

	def get_queryset(self):
		return super(AliasManager, self).get_queryset().filter(type=Catalog.ALIAS)


class Alias(Catalog):
	objects = AliasManager()

	class Meta:
		verbose_name = 'Алиас'
		verbose_name_plural = 'Алиасы'
		proxy = True

	def save(self, *args, **kwargs):
		for item in SlugCategory.objects.filter(category=self):
			for i in ['', '-1', '-2', '-3']:
				cache.delete(f'render_to_string_/{item.slug}/{i}')
		try:
			self.type = self.ALIAS
			return super(Catalog, self).save(*args, **kwargs)
		except:
			pass


	def get_key_slug(self, domain=None):
		class_name = self.__class__.__name__
		if class_name in ['Page', 'BasePage']:
			class_name = 'Page'
		return f"{domain.domain + '_' if domain else ''}{class_name}_{self.id}"

	def get_absolute_url(self, *args, **kwargs):
		domain = get_request().domain
		try:
			slug, _ = self.slugs.get_or_create(domain=domain, defaults={'slug': slugify(self.title)})
			return reverse('pages:page_detail', args=[slug.slug])
		except Exception as exception:
			print('404 generated', exception)
			raise Http404
		return reverse('category', args=[self.encode_slug(domain=domain)])


class AliasAttribute(models.Model):
	category = models.ForeignKey('catalog.Catalog', verbose_name="Категория", on_delete=models.CASCADE,
								 related_name='alias_attrs')
	attribute = models.ForeignKey('catalog.ProductAttribute', verbose_name="Атрибут",
								  on_delete=models.CASCADE, related_name='alias_attrs')
	value = models.ManyToManyField('catalog.AttributeValue', blank=True, symmetrical=False)
	min_value = models.PositiveIntegerField('Минимальное значение', default=0, blank=True)
	max_value = models.PositiveIntegerField('Максимальное значение', default=0, blank=True)
	sort = models.PositiveSmallIntegerField('Сортировка', default=0)

	class Meta:
		verbose_name = 'Атрибут алиаса'
		verbose_name_plural = 'Атрибуты алиаса'
		ordering = ['sort']

	def __str__(self):
		return self.attribute.__str__()

	def get_value(self):
		if self.value:
			return self.value
		response = {}
		if self.min_value:
			response['min_value'] = self.min_value
		if self.max_value:
			response['max_value'] = self.max_value
		return response


class CategoryAttribute(models.Model):
	# пустые значения показываются при поиске
	category = models.ForeignKey('catalog.Catalog', verbose_name="Категория", on_delete=models.CASCADE,
								 related_name='attrs', blank=True, null=True)
	attribute = models.ForeignKey('catalog.ProductAttribute', verbose_name="Атрибут",
								  on_delete=models.CASCADE, related_name='category_attrs')
	sort = models.PositiveSmallIntegerField('Сортировка', default=0)

	class Meta:
		ordering = ['sort']
		verbose_name = 'Атрибут категории'
		verbose_name_plural = 'Атрибуты категорий'
		unique_together = ['category', 'attribute']

	def __str__(self):
		return self.attribute.__str__()


class MessageCategory(RecipientMixin, models.Model):
	category = models.ForeignKey('catalog.Category', verbose_name="Категория", on_delete=models.CASCADE,
								 related_name='messages')
	domain = models.ForeignKey('domains.Domain', verbose_name='Город', on_delete=models.CASCADE)

	class Meta:
		ordering = ['domain']
		verbose_name = 'Уведомление'
		verbose_name_plural = 'Уведомления'
		unique_together = ['category', 'domain']

	def __str__(self):
		return f'{self.id}'


class SeoCategory(SeoBase):
	domain = models.ForeignKey('domains.Domain', verbose_name="Домен", on_delete=models.CASCADE)
	category = models.ForeignKey('catalog.Catalog', verbose_name="Категория", on_delete=models.CASCADE,
								 related_name='seo')
	meta_message = RichTextUploadingField('Текст на странице', blank=True, default="")

	class Meta:
		ordering = ['id']
		verbose_name = 'SEO'
		verbose_name_plural = 'SEO'
		unique_together = ['domain', 'category']

	def __str__(self):
		return self.category.__str__()


class SlugCategory(models.Model):
	domain = models.ForeignKey('domains.Domain', verbose_name="Домен", on_delete=models.CASCADE)
	category = models.ForeignKey('catalog.Catalog', verbose_name="Категория", on_delete=models.CASCADE,
								 related_name='slugs')
	slug = models.SlugField('Слаг', max_length=250)

	class Meta:
		ordering = ['id']
		verbose_name = 'Урл'
		verbose_name_plural = 'Урлы'
		unique_together = [['domain', 'category'], ['domain', 'category', 'slug']]

	def __str__(self):
		return self.slug


class AlterSeoCategory(models.Model):
	category = models.ManyToManyField('catalog.Catalog', verbose_name='Категории', related_name='alter_seo_cats')
	# bool fields
	category_exclude = models.ManyToManyField('catalog.Catalog', verbose_name='Категории-исключения')
	# text fields
	alter_seo_title_product = models.TextField('Альтернативный СЕО заголовок (товары)', blank=True, null=True)
	alter_seo_desc_product = models.TextField('Альтернативный СЕО текст (товары)', blank=True, null=True)
	alter_seo_title_category = models.TextField('Альтернативный СЕО заголовок (категории)', blank=True, null=True)
	alter_seo_desc_category = models.TextField('Альтернативный СЕО текст (категории)', blank=True, null=True)

	def __str__(self):
		return f'Альтернативное СЕО'

	class Meta:
		verbose_name = 'Альтер СЕО'
		verbose_name_plural = 'Альтер СЕО'


@receiver(post_save, sender=Catalog)
@receiver(post_save, sender=Category)
@receiver(post_save, sender=Alias)
def update_attrs_category(instance, **kwargs):
	"""Прокидывание атрибутов категорий для родителей или детей"""
	if instance:
		
		if instance.dont_save_attrs_parent or not instance.parent:
			instance.saved_attrs_parent = False

		if instance.saved_attrs_parent:
			try: instance.update_attrs(attrs=instance.parent.attrs.all(), items=[instance])
			except:
				raise

		if instance.saved_attrs_children:
			instance.update_attrs(items=instance.get_descendants())

		if instance.discount_brands_save_child:
			print(instance, "save category brands")
			instance.update_brands_discount()


@receiver(m2m_changed, sender=Catalog.discount_brands.through)
@receiver(m2m_changed, sender=Category.discount_brands.through)
@receiver(m2m_changed, sender=Alias.discount_brands.through)
def update_attrs_category(instance, **kwargs):
	"""Прокидывание атрибутов категорий для родителей или детей"""
	if instance:
		
		if instance.dont_save_attrs_parent or not instance.parent:
			instance.saved_attrs_parent = False

		if instance.saved_attrs_parent:
			try: instance.update_attrs(attrs=instance.parent.attrs.all(), items=[instance])
			except:
				raise

		if instance.saved_attrs_children:
			instance.update_attrs(items=instance.get_descendants())

		if instance.discount_brands_save_child:
			print(instance, "m2m changed")
			instance.update_brands_discount()



@receiver(post_save, sender=Catalog)
@receiver(post_save, sender=Category)
@receiver(post_save, sender=Alias)
def update_slug(instance, created, sender, **kwargs):
	"""очистка кэша слагов"""
	keys = []
	for domain in Domain.objects.all():
		keys += ['{}_cached_categories'.format(domain)]
	cache.delete_many(keys)
	if created and hasattr(instance, 'get_family'):
		keys = []
		for item in instance.get_family():
			if hasattr(item, 'get_key_slug'):
				key = item.get_key_slug()
				keys += [key]
		cache.delete_many(keys)


@receiver(pre_save, sender=Catalog)
@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=Alias)
def pre_update_slug(instance, sender, **kwargs):
	"""Очистка кэша фильтров"""
	old = sender.objects.filter(id=instance.id).first()
	keys = []
	if old and old.parent != instance.parent:
		domains = Domain.objects.all()
		for obj in [o for o in [old.parent, instance.parent] if o]:
			for item in obj.get_descendants(include_self=True):
				if hasattr(item, 'get_key_slug'):
					for domain in domains:
						keys += [item.get_key_slug(domain)]
			for item in obj.get_family():
				if hasattr(item, 'get_key_slug'):
					for domain in domains:
						keys += [item.get_key_slug(domain)]

	keys += [f'template_filters_{instance.id}', f'filters_{instance.id}']
	cache.delete_many(keys)


@receiver(post_save, sender=Alias)
def save_products_for_alias(instance, sender, **kwargs):
	"""При сохранения алиаса сразу привязываем к нему продукты"""
	request = get_request()
	Product = apps.get_model('catalog', 'Product')
	if instance.is_active:
		if instance.parent:
			qs = instance.parent.get_products()
		else:
			qs = Product.objects.active()
		filter_class = ProductFilterSEF(qs, request, alias=instance)
		products = filter_class.filter().filter(domain__in=instance.domain.all()).distinct()
		instance.alias_products.set(products)
	else:
		instance.alias_products.clear()
	instance.clear_fpp_cache()
	instance._tree_manager.rebuild()


@receiver(post_save, sender=Catalog)
def save_products_for_alias(instance, sender, **kwargs):
	"""При сохранения алиаса сразу привязываем к нему продукты"""
	path = instance.get_absolute_url()
	print("Category path", path)
	print('Regex', F"get-context-data-filters-for-/category_products/products{path}*")
	keys = cache.keys(F"get-context-data-filters-for-/category_products/products{path}*")
	print("Keys", keys)
	for key in keys:
		cache.delete(key)