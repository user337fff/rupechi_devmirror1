from pathlib import Path
import datetime

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core import management
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Settings
from .ordersXML import OrdersXmlGenerator
from ..shop.models import Order, EndPoint


@method_decorator(csrf_exempt, name='dispatch')
class Exchange1cView(View):
	"""
	Класс для обмена с 1с
	На вход принимает объект request
	В зависимости от параметра mode вызываем метод класса
	"""
	FOLDER_NAME = '1c'
	FOLDER_PATH = Path(settings.BASE_DIR) / '../' / FOLDER_NAME

	FOLDER_IMAGES_NAME = 'products'
	FOLDER_IMAGES_PATH = (Path(settings.BASE_DIR) /
						  settings.MEDIA_ROOT /
						  FOLDER_IMAGES_NAME)

	MODES = ['checkauth', 'init', 'file', 'import', 'query', 'success']

	def init(self):
		self.response = HttpResponse()
		self.params = self.request.GET
		self.mode = self.params.get('mode', '')

	def _method(self, request, *args, **kwargs):
		self.init()
		# определяем есть ли метод в списке методов
		if self.mode in self.MODES:
			handler = getattr(self, f'_{self.mode}')
			handler()
		else:
			self.response.write(
				f'Ошибка. Некорректный метод mode: {self.mode}')
		return self.response

	def get(self, request, *args, **kwargs):
		return self._method(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		return self._method(request, *args, **kwargs)

	def _checkauth(self):
		# type = self.params.get('type')
		# if type == 'catalog':
		token = get_token(self.request)
		self.response.write(
			'success\n'
			'csrftoken\n'
			f'{token}\n'
			'sessid=6dff9e4879b775e811d5e18dcc615412\n'
			'timestamp=1527775445')
		# elif type == 'sale': # are you idiot? do you even read the specs?
		#	 self._query()
		# else:
		#	 self.response.write(f'Ошибка. Неверно указан тип: {type}.')

	def _init(self):
		self.response.write("zip=no\nfile_limit=1073741824")

	def _file(self):
		filename = self.params.get('filename')
		print(f'=====1C FILENAME  {filename}')
		if not filename:
			self.response.write('Ошибка. Не задано имя файла.')
			return
		# определяем каталог для сохранения в зависимости от расширения
		if filename.endswith('.xml'):
			file_path = self.FOLDER_PATH / filename
		else:
			file_path = self.FOLDER_IMAGES_PATH / filename
		if len(file_path.parents) > 1:
			# создаем родительские директории
			file_path.parent.mkdir(parents=True, exist_ok=True)
		# сохраняем файл
		with open(file_path, 'wb') as outfile:
			outfile.write(self.request.body)
		# Создаем копию файлов импорт и офферс с добавление к названию времени в ISO формате
		if filename in ('import0_1.xml', 'offers0_1.xml'):
			iso_time = str(datetime.datetime.now().astimezone().replace(microsecond=0).isoformat())
			copy_filename = f'../1c/{filename[:-4]}_{iso_time}.xml'
			with open(copy_filename, 'wb') as copyfile:
				copyfile.write(self.request.body)
		self.response.write("success")

	def _import(self):
		type = self.params.get('type')
		if type == 'catalog':  # do not even try to import orders befour you check and fix import1c.py
			filename = self.params.get('filename')
			if not filename:
				self.response.write('Ошибка. Не задано имя файла')
				return
			if filename.endswith('.xml'):
				management.call_command('import1c', filename=filename)
		self.response.write("success")

	def _query(self):
		type = self.params.get('type')
		if type == 'sale':
			self.response = OrdersXmlGenerator().generate_sales(**self.kwargs)
		else:
			self.response.write(f'Ошибка. Неверно указан тип: {type}')

	def _success(self):
		type = self.params.get('type')
		#endpoint = self.kwargs.get('postfix')
		if type == 'sale':
			last_date = Settings.load()
			last_date.last_export_date = timezone.now()
			last_date.save(update_fields=['last_export_date'])

			#endpoint = EndPoint.objects.get(slug=endpoint)
			#orders = Order.objects.filter(status_export=Order.EXCHANGE_STATUS_PROCESSING)[:20]
			#orders = endpoint.filter(orders)
			#orders.update(status_export=Order.EXCHANGE_STATUS_EXPORTED)
			
			self.response.write("success")
		else:
			self.response.write(f'Ошибка. Неверно указан тип: {type}')


@permission_required('exchange1c.change_settings', raise_exception=True)
def orders_xml_debug(request, postfix=''):
	return OrdersXmlGenerator(postfix=postfix).generate_sales(debug=True)
